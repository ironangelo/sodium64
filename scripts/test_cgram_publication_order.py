"""Independent publication slots; real missing, late and wrong-source controls."""
import unittest
from test_gate_c_cgram_rsp_consumer_impl_clean import ROOT,prove_main_publication

class PublicationOrderTests(unittest.TestCase):
    def setUp(self):self.source=(ROOT/'src/main.S').read_text()

    def test_current_publications(self):prove_main_publication(self.source)

    def test_independent_main_and_window_slot_order(self):
        source=self.source
        a=source.index('    la t0, rsp_mode7_window_text_start')
        b=source.index('    la t0, rsp_mode7_text_start',a)
        c=source.index('    la t0, rsp_main_text_start',b)
        d=source.index('    la t0, rsp_hcomp_text_start',c)
        changed=source[:a]+source[c:d]+source[b:c]+source[a:b]+source[d:]
        prove_main_publication(changed)

    def test_missing_renderer_slot_rejected(self):
        changed=self.source.replace('    sw t0, DMEM(OVERLAY_MAIN_SRC)\n','',1)
        with self.assertRaisesRegex(AssertionError,'renderer publication'):prove_main_publication(changed)

    def test_wrong_main_source_rejected(self):
        # R43 also loads Main for its immutable no-span copy. Mutate the
        # actual renderer publication rather than that unrelated earlier load.
        binding='    la t0, rsp_main_text_start\n    addi t0, t0, 0x3A8\n'
        self.assertEqual(self.source.count(binding),1,'unique Main publication source')
        changed=self.source.replace(binding,binding.replace('rsp_main_text_start','rsp_hcomp_text_start'),1)
        self.assertNotEqual(changed,self.source,'negative mutation must execute')
        with self.assertRaisesRegex(AssertionError,'source binding'):prove_main_publication(changed)

    def test_late_raw_shadow_rejected(self):
        store='    sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS + 4)\n'
        reset='    sw zero, 0xA4080000 // SP_PC\n'
        changed=self.source.replace(store,'',1).replace(reset,reset+store,1)
        with self.assertRaisesRegex(AssertionError,'raw-shadow publication'):prove_main_publication(changed)

    def test_raw_pointer_store_before_load_rejected(self):
        pair='    li t0, HCOMP_RAW_PALETTE_QUEUE1\n    sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS)'
        changed=self.source.replace(pair,'    sw t0, DMEM(HCOMP_RAW_PALETTE_PTRS)\n    li t0, HCOMP_RAW_PALETTE_QUEUE1',1)
        with self.assertRaisesRegex(AssertionError,'ordering'):prove_main_publication(changed)

if __name__=='__main__':unittest.main()
