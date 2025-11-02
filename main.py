from typing import List
from BitPacker import bit_packer_factory
import random
import unittest

def generate_int_list() -> List[int]:
    return (
        [random.randint(0, 9999) for _ in range(4500)] +
        [random.randint(9999, 99999) for _ in range(4500)] +
        [random.randint(99999, 999999) for _ in range(1000)]
    )

class TestBitPacker(unittest.TestCase):

    def test_bit_packer_crossing(self) -> None:
        array: List[int] = generate_int_list()
        packer = bit_packer_factory('crossing', array)
        packer.compress()

        unpacker = bit_packer_factory('crossing', [])
        ints: List[int] = unpacker.uncompress(packer.compressed)

        self.assertEqual(packer.total_items, unpacker.total_items, 'Total items does not match')
        self.assertEqual(packer.best_bit_length, unpacker.best_bit_length, 'Best bit length does not match')
        self.assertEqual(packer.total_overflow, unpacker.total_overflow, 'Total overflow does not match')
        self.assertEqual(packer.max, unpacker.max, 'Max does not match')
        self.assertEqual(array, ints, 'Uncompress failed as arrays are not the same')
        for i in range(0, 10):
            random_key = random.randint(0, len(array))
            self.assertEqual(array[random_key], packer.get(random_key), 'Unable to retrieve correct number for key ' + str(random_key))

        for key in packer.benchmark.keys():
            print('[bench packer crossing] ', key, ' took ', packer.benchmark[key], 'seconds')

        for key in unpacker.benchmark.keys():
            print('[bench unpacker crossing] ', key, ' took ', unpacker.benchmark[key], 'seconds')

        bandwidth = 1e6
        latency = 0.05
        is_worthwhile = packer.is_compression_better(bandwidth, latency)
        if is_worthwhile:
            print('[bench packer crossing] compression worth it')
        else:
            print('[bench packer crossing] compression does not worth it')

    def test_bit_packer_no_crossing(self) -> None:
        array: List[int] = generate_int_list()
        packer = bit_packer_factory('nocrossing', array)
        packer.compress()

        unpacker = bit_packer_factory('nocrossing', [])
        ints: List[int] = unpacker.uncompress(packer.compressed)

        self.assertEqual(packer.total_items, unpacker.total_items, 'Total items does not match')
        self.assertEqual(packer.best_bit_length, unpacker.best_bit_length, 'Best bit length does not match')
        self.assertEqual(packer.total_overflow, unpacker.total_overflow, 'Total overflow does not match')
        self.assertEqual(packer.max, unpacker.max, 'Max does not match')
        self.assertEqual(array, ints, 'Uncompress failed as arrays are not the same')
        for i in range(0, 10):
            random_key = random.randint(0, len(array))
            self.assertEqual(array[random_key], packer.get(random_key), 'Unable to retrieve correct number for key ' + str(random_key))

        for key in packer.benchmark.keys():
            print('[bench packer nocrossing] ', key, ' took ', packer.benchmark[key], 'seconds')

        for key in unpacker.benchmark.keys():
            print('[bench unpacker nocrossing] ', key, ' took ', unpacker.benchmark[key], 'seconds')

        bandwidth = 1e6
        latency = 0.05
        is_better = packer.is_compression_better(bandwidth, latency)
        if is_better:
            print('[bench packer nocrossing] compression worth it')
        else:
            print('[bench packer nocrossing] compression does not worth it')

if __name__ == '__main__':
    unittest.main()