"""Offline application-boundary tests. No SDK/Streamlit installation or API calls.
AST extraction executes the actual application functions/handlers. It does not
verify Streamlit WebSockets, Google SDK internals, hosting logs or native Office.
All credential-like test values are synthetic, never valid provider keys.
"""
import ast
import contextlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
TUKUYI = 'validate_and_discover_gemini' in SOURCE
CANARY = 'SYNTHETIC_BYOK_CANARY_NOT_A_REAL_KEY'

class State(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def execute(nodes, namespace):
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(ROOT / 'app.py'), 'exec'), namespace)


class ByokSecurityTests(unittest.TestCase):
    def setUp(self):
        # Deny network even if a future edit accidentally adds one.
        self.network = patch('socket.socket', side_effect=AssertionError('OFFLINE_ONLY'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.state = State(api_key=CANARY, api_key_valid=False, api_error=None,
                           model_name='gemini-2.0-flash', available_models=[])
        self.messages = []
        self.st = types.SimpleNamespace(session_state=self.state,
            error=self.messages.append, warning=self.messages.append)
        self.models = Mock()
        self.models.generate_content.return_value = types.SimpleNamespace(text='SAFE_REPLY')
        self.models.list.return_value = []
        genai = types.ModuleType('google.genai')
        genai.Client = Mock(return_value=types.SimpleNamespace(models=self.models))
        genai.types = types.SimpleNamespace(GenerateContentConfig=lambda **kw: kw)
        google = types.ModuleType('google')
        google.genai = genai
        self.genai = genai
        self.imports = patch.dict(sys.modules, {'google': google, 'google.genai': genai})
        self.imports.start()
        self.addCleanup(self.imports.stop)
        self.ns = {'st': self.st, 'DEFAULT_MODELS': ['gemini-1.5-flash', 'gemini-2.0-flash']}
        execute([n for n in TREE.body if isinstance(n, ast.FunctionDef)], self.ns)
        self.validate = self.ns['validate_and_discover_gemini' if TUKUYI else 'validate_api_key']

    def test_constructor_failure_never_copies_exception_to_state_or_output(self):
        self.genai.Client.side_effect = RuntimeError('request header=' + CANARY)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            self.assertIsNone(self.ns['get_gemini_client'](CANARY))
        self.assertTrue(self.state.api_error)
        self.assertNotIn(CANARY, str(self.state.api_error) + out.getvalue())

    def test_validation_failure_does_not_publish_raw_payload(self):
        self.models.list.side_effect = RuntimeError(CANARY)
        self.models.generate_content.side_effect = RuntimeError('secret URL=' + CANARY)
        self.assertFalse(self.validate(CANARY))
        self.assertNotIn(CANARY, str(self.state.api_error))

    def test_password_normalization_and_successful_validation(self):
        self.assertTrue(self.validate('  "' + CANARY + '"  '))
        self.genai.Client.assert_called_once_with(api_key=CANARY)
        self.assertIsNone(self.state.api_error)
        self.assertEqual(self.models.generate_content.call_args.kwargs['contents'], 'PING')

    def test_blank_key_does_not_initialize_sdk(self):
        self.assertFalse(self.validate('   '))
        self.genai.Client.assert_not_called()

    def test_all_ui_exception_sinks_hide_injected_secret(self):
        count = 0
        for handler in (n for n in ast.walk(TREE) if isinstance(n, ast.ExceptHandler)):
            for statement in handler.body:
                # Execute actual error/warning sink statements without UI startup.
                if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                    fn = statement.value.func
                    if isinstance(fn, ast.Attribute) and fn.attr in ('error', 'warning'):
                        with self.subTest(line=statement.lineno):
                            self.messages.clear()
                            execute([statement], {'st': self.st, 'e': RuntimeError(CANARY)})
                            self.assertTrue(self.messages)
                            self.assertNotIn(CANARY, str(self.messages))
                        count += 1
        self.assertGreater(count, 0)

    @unittest.skipIf(TUKUYI, 'STP generation wrapper only')
    def test_generation_keeps_prompt_and_fallback_behavior(self):
        self.models.generate_content.side_effect = [RuntimeError('first unavailable'),
                                                     types.SimpleNamespace(text='SAFE_REPLY')]
        result = self.ns['generate_content_with_fallback']('SAFE_PROMPT', 'SAFE_SYSTEM', True)
        self.assertEqual(result, 'SAFE_REPLY')
        self.assertEqual(self.models.generate_content.call_count, 2)
        kw = self.models.generate_content.call_args.kwargs
        self.assertEqual(kw['contents'], 'SAFE_PROMPT')
        self.assertEqual(kw['config']['response_mime_type'], 'application/json')
        self.assertNotIn(CANARY, str(kw))

    @unittest.skipIf(TUKUYI, 'STP generation wrapper only')
    def test_exhausted_generation_raises_safe_exception(self):
        self.models.generate_content.side_effect = RuntimeError(CANARY)
        with self.assertRaises(Exception) as result:
            self.ns['generate_content_with_fallback']('SAFE_PROMPT')
        self.assertNotIn(CANARY, str(result.exception))

    @unittest.skipUnless(TUKUYI, 'Tukuyi discovery only')
    def test_discovery_success_avoids_ping(self):
        self.models.list.return_value = [types.SimpleNamespace(name='models/gemini-2.0-flash',
                                          supported_generation_methods=['generateContent'])]
        self.assertTrue(self.validate(CANARY))
        self.models.generate_content.assert_not_called()
        self.assertTrue(self.state.api_key_valid)

    def test_actual_export_payload_excludes_authentication_state(self):
        import export_helpers as exports
        import sample_data
        if TUKUYI:
            node = next(n for n in ast.walk(TREE) if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'proposal_result' for t in n.targets))
            names = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
            env = {name: 'SAFE_PROJECT - SAFE_PRODUCT' for name in names}
            env.update(st=self.st, sync_p1_p2=False, summary_final='SAFE_SUMMARY')
            execute([node], env)
            payload = env['proposal_result']
        else:
            self.state.update(sample_data.SAMPLE_CASES['collaboration_hub'])
            node = next(n for n in ast.walk(TREE) if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'full_state' for t in n.targets))
            env = {'st': self.st}
            execute([node], env)
            payload = env['full_state']
        results = [exports.export_proposal_json(payload), exports.export_proposal_markdown(payload)]
        if TUKUYI:
            results += [exports.generate_standalone_html_deck(payload), exports.export_virtual_sales_csv()]
        for output in results:
            self.assertNotIn(CANARY, output)
        self.assertNotIn('api_key', payload)

    @unittest.skipUnless(TUKUYI, 'Tukuyi PPTX only')
    def test_pptx_requests_have_separate_buffers_and_no_disk_access(self):
        # Execute the real download block; replace only the external PPTX writer.
        nodes = next(n.body for n in ast.walk(TREE) if isinstance(n, ast.If)
                     and 'current_proposal' in ast.unparse(n.test) and any(
                         isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'pptx_filename'
                         for t in x.targets) for x in n.body))
        start = next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id == 'pptx_filename' for t in n.targets))
        end = next((i for i in range(start+1,len(nodes)) if isinstance(nodes[i],ast.Expr)
                    and isinstance(nodes[i].value,ast.Call) and ast.unparse(nodes[i].value.func)=='st.markdown'),len(nodes))
        from datetime import datetime
        downloads, buffers = [], []
        def writer(data, destination):
            self.assertIsInstance(destination, io.BytesIO)
            buffers.append(destination)
            destination.write(data['summary'].encode())
            return True
        for label in ('SESSION_A', 'SESSION_B'):
            env = {'io':io, 'os':__import__('os'), '__file__':str(ROOT/'app.py'),
                   'datetime':datetime, 'p_data':{'summary':label}, 'build_tukuyi_pptx':writer,
                   'col_down4':types.SimpleNamespace(download_button=lambda **kw: downloads.append(kw['data']),info=lambda *a:None),
                   'st':self.st}
            with patch('builtins.open', side_effect=AssertionError('PPTX_MUST_NOT_USE_DISK')):
                execute(nodes[start:end], env)
        self.assertEqual(downloads, [b'SESSION_A', b'SESSION_B'])
        self.assertIsNot(buffers[0], buffers[1])

if __name__ == '__main__':
    unittest.main(verbosity=2)
