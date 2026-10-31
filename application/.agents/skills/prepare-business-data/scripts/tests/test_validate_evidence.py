import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("validate_evidence", ROOT/"scripts/validate_evidence.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = module.build_validator()
        cls.examples = [json.loads(line) for line in (ROOT/"references/evidence-examples.jsonl").read_text().splitlines()]

    def test_all_supported_locator_examples_validate(self):
        for item in self.examples:
            self.assertEqual(module.item_errors(item,self.validator), [],item['id'])

    def test_reference_labels_cannot_enter_builder_input(self):
        item = copy.deepcopy(self.examples[-2]);item['quality']['modeling_access']='allowed'
        self.assertTrue(module.item_errors(item,self.validator))

    def test_unlocatable_text_cannot_be_success(self):
        item = copy.deepcopy(self.examples[-1]);item['quality']['status']='success'
        self.assertTrue(module.item_errors(item,self.validator))

    def test_database_record_requires_stable_locator(self):
        item = copy.deepcopy(self.examples[1]);item['locator']={'type':'database','table':'visits'}
        self.assertTrue(module.item_errors(item,self.validator))
        item['locator'].update(row_ordinal=1,query_id='frozen-query',identity_scope='snapshot')
        self.assertEqual(module.item_errors(item,self.validator),[])

    def test_pdf_coordinates_need_units_and_origin(self):
        item = copy.deepcopy(self.examples[6]);del item['locator']['origin']
        self.assertTrue(module.item_errors(item,self.validator))

    def test_waveform_units_match_channels(self):
        item = copy.deepcopy(self.examples[9]);item['content']['metadata']['units']=['mV']
        self.assertTrue(module.item_errors(item,self.validator))

    def test_incompatible_locator_returns_error_without_reading_missing_payload(self):
        item=copy.deepcopy(self.examples[1])
        item['locator']=copy.deepcopy(self.examples[9]['locator'])
        self.assertTrue(module.item_errors(item,self.validator))

    def test_duplicate_ids_and_bounded_input_do_not_report_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'items.jsonl'
            p.write_text((json.dumps(self.examples[0])+'\n')*2)
            result=module.validate_file(p)
            self.assertFalse(result['ok'])
            self.assertEqual(result['errors'][0]['rule'],'duplicate_id_in_checked_batch')
            result=module.validate_file(p,max_items=1)
            self.assertFalse(result['ok']);self.assertTrue(result['input_truncated'])

    def test_validation_errors_do_not_echo_business_text(self):
        item=copy.deepcopy(self.examples[4]);item['quality']['status']='private-business-value'
        errors=module.item_errors(item,self.validator)
        self.assertNotIn('private-business-value',json.dumps(errors))


if __name__ == '__main__':
    unittest.main()
