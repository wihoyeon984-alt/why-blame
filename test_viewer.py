import io
import sys
import viewer
import unittest

class TestViewer(unittest.TestCase):
    def test_render_card_survives_cp949_output(self):
        buffer = io.BytesIO()
        cp949_stdout = io.TextIOWrapper(buffer, encoding='cp949')
        original_stdout = sys.stdout
        sys.stdout = cp949_stdout
        try:
            viewer.render_card(
                'example.py',
                '1-2',
                ('owner', 'repo'),
                ['print("hello")'],
                [{'hash': 'abcdef123456', 'date': '2026-10-03', 'type': 'FIX', 'message': 'test change', 'diff_lines': [], 'ref_items': []}],
                {'score': 3, 'has_message': True, 'has_diff': True, 'has_refs': False, 'has_context': False, 'coverage': 'HIGH', 'strength': 'HIGH', 'consistency': 'HIGH', 'ambiguity': 'LOW', 'confidence': 'HIGH', 'limitations': []},
            )
        finally:
            sys.stdout = original_stdout
        cp949_stdout.flush()
        output = buffer.getvalue().decode('cp949')
        self.assertIn('WHY-BLAME', output)
