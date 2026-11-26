import io
import math
import unittest
from array import array
from ast import literal_eval
from fractions import Fraction
from struct import unpack
from zipfile import ZipFile

from nightecho.nfle25_envelopes import prepare_envelope, write_npy
from nightecho.waveform import Waveform


class Nfle25EnvelopeTests(unittest.TestCase):
    def test_envelope_keeps_epoch_grid_and_masks_a_rail_hit(self):
        values = array("d", (math.sin(math.tau * 20 * i / 64) for i in range(3840)))
        values[20 * 64] = 250
        waveform = Waveform("TIB Sx", "mV", Fraction(64), -250, 250, values)
        envelope, excluded = prepare_envelope(waveform, 2)
        self.assertEqual(excluded, [0])
        self.assertEqual(len(envelope), 600)
        self.assertTrue(all(math.isnan(value) for value in envelope[:300]))
        self.assertTrue(all(value > 100 for value in envelope[300:]))

    def test_numpy_header_and_byte_order(self):
        archive_data = io.BytesIO()
        with ZipFile(archive_data, "w") as archive:
            write_npy(archive, "stage", "|S7", (1,), b"unknown")
        with ZipFile(archive_data) as archive:
            data = archive.read("stage.npy")
        self.assertEqual(data[:8], b"\x93NUMPY\x01\x00")
        header_end = 10 + unpack("<H", data[8:10])[0]
        self.assertEqual(header_end % 64, 0)
        self.assertEqual(literal_eval(data[10:header_end].decode("ascii")),
                         {"descr": "|S7", "fortran_order": False, "shape": (1,)})
        self.assertEqual(data[header_end:], b"unknown")
