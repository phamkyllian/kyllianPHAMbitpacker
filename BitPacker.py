import math
import time
from typing import List

#####
# Classe de base implémentant les méthodes partagtées
# entre les deux méthodes crossing et nocrossing
#####
class BaseBitPacker:
    # Initialisation en envoyer le tableau à compresser en paramètre
    def __init__(self, array: List[int] = []):
        self.array = array
        self.max = 0
        self.compressed = []
        self.words = []
        self.lengths = []
        self.meta_words_length = (32).bit_length()
        self.words_length = 32
        self.total_overflow = 0
        self.total_items = 0
        self.best_bit_length = 0
        self.crossing = True
        self.benchmark: dict[str, int] = {}

        # Initialisation des valeurs si le tableau n'est pas vide
        if len(array) > 0:
            self._set_array_bit_lengths()
            self._set_array_max_bit_length()
            self._find_best_bit_length()
            self._set_total_items()

    @staticmethod
    def _int_to_bits(number: int, length: int):
        return bin(number)[2:].zfill(length)

    @staticmethod
    def _bits_to_int(bits: str) -> int:
        return int(bits, 2)

    def _set_array_max_bit_length(self):
        if not self.lengths:
            self._set_array_bit_lengths()
        lengths = self.lengths
        lengths.sort()
        self.max = max(lengths)

    def _set_array_bit_lengths(self):
        self.lengths = [number.bit_length() for number in self.array]

    def _set_total_items(self):
        self.total_items = len(self.array)

    # Calcul du meilleur bit pour compresser
    def _find_best_bit_length(self):
        start = time.perf_counter()
        best_bit_length: int = 1
        number_of_words: int = 0
        # Le meilleur nombre se trouve entre 1 et le nombre maximum
        # de bits utilisés pour écrire les overflow
        for nb in range(1, self.max):
            nb_length: int = 0
            # On calcul le nombre total d'overflow qu'il y aura pour ce nombre
            # si les nombres total d'overflow est supérieur au nombre en question
            # on continue la boucle car on ne pourra pas écrire la position de l'overflow
            total_overflow = len([n for n in [number.bit_length() for number in self.array] if n > nb])
            if total_overflow.bit_length() > nb:
                continue

            # On calcul le nombre total de bits qui seront utilisés pour écrire
            # tous les nombres du tableau
            for number in self.array:
                length = number.bit_length()
                if length > nb:
                    nb_length += nb + 1 + self.max
                else:
                    nb_length += nb + 1

            # On sélectionne le nombre de bit le plus bas qui est apparu
            if number_of_words == 0 or math.ceil(nb_length / 32) <= number_of_words:
                best_bit_length = nb
                number_of_words = math.ceil(nb_length / 32)

        self.best_bit_length = best_bit_length
        end = time.perf_counter()
        self._add_timer('find_best_bit_length', f"{end - start:.6f}")

    # Lecture des meta (nombre total d'entier, maximum de bits
    # nombre total d'overflow)
    def _read_meta(self, phrase: str) -> int:
        start = time.perf_counter()
        cursor: int = 0
        self.total_items = self._bits_to_int(phrase[cursor:32])
        cursor += 32
        self.best_bit_length = self._bits_to_int(phrase[cursor:(cursor + self.meta_words_length)])
        cursor += self.meta_words_length
        self.max = self._bits_to_int(phrase[cursor:(cursor + self.meta_words_length)])
        cursor += self.meta_words_length
        self.total_overflow = self._bits_to_int(phrase[cursor:(cursor + 32)])
        cursor += 32
        end = time.perf_counter()
        self._add_timer('read_meta', f"{end - start:.6f}")
        return cursor

    # Ecriture des meta
    def _write_meta(self) -> str:
        start = time.perf_counter()
        phrase: str = ''
        phrase += self._int_to_bits(self.total_items, 32)
        phrase += self._int_to_bits(self.best_bit_length, self.meta_words_length)
        phrase += self._int_to_bits(self.max, self.meta_words_length)
        end = time.perf_counter()
        self._add_timer('writing_meta', f"{end - start:.6f}")
        return phrase

    # Liste des overflows uniques (on ne rajoute pas un nombre
    # déjà listé deux fois à la fin de la chaine)
    def _get_overflow_list(self) -> dict[int, int]:
        start = time.perf_counter()
        overflow_list: dict[int, int] = {}
        suffix_position = 0
        # On parcourt chaque entier de la liste ; s'il est plus grand que le best_bit_length, 
        # on l'ajoute à la liste des overflows
        for number in self.array:
            bit_length = number.bit_length()
            if bit_length > 32:
                raise ValueError("Integer is larger than 32 bits")

            if bit_length > self.best_bit_length and overflow_list.get(number) is None:
                overflow_list[number] = suffix_position
                suffix_position += 1
        end = time.perf_counter()
        self._add_timer('overflow_list', f"{end - start:.6f}")
        return overflow_list

    def _add_timer(self, code, time) -> None:
        self.benchmark[code] = time

    def is_compression_better (self, bandwidth: float, latency: float) -> bool:
        compressed_size_bytes: int = len(self.compressed) * 4
        compression_time: float = float(self.benchmark.get("compression", 0))
        decompression_time: float = float(self.benchmark.get("decompression", 0))
        raw_time: float = latency + (len(self.array) * 4) / bandwidth
        compressed_time: float = latency + compression_time + compressed_size_bytes / bandwidth + decompression_time
        return compressed_time < raw_time

#####
# BitPacker avec "crossing" (les bits sont écris les un à la suite des autres
# sans préocupation pour leur continuité)
#####
class BitPackerCrossing(BaseBitPacker):
    def compress(self):
        if not len(self.array):
            raise "no array has been given, cannot compress"
        start = time.perf_counter()
        # On écrit les métadonnées
        phrase: str = self._write_meta()
        overflow_list = self._get_overflow_list()
        # On écrit dans "suffix" tous les entiers overflow
        suffix = "".join([self._int_to_bits(key, self.max) for key in overflow_list.keys()])

        self.total_overflow = len(overflow_list)
        phrase += self._int_to_bits(self.total_overflow, 32)

        # On écrit soit l'entier, soit la position de l'overflow
        for number in self.array:
            bit_length = number.bit_length()
            if bit_length <= self.best_bit_length:
                phrase += "0" + self._int_to_bits(number, self.best_bit_length)
            else:
                phrase += "1" + self._int_to_bits(overflow_list.get(number), self.best_bit_length)

        # On ajoute les overflow
        phrase += suffix
        # On ajoute des "0" à la fin pour que le dernier entier compressé soit correct
        padding_length = (32 - len(phrase) % 32) % 32
        phrase += "0" * padding_length

        # Maintenant que nous avons la suite de bits, on écrit les entiers de 32 bits
        self.words = [phrase[i:i + self.words_length] for i in range(0, len(phrase), self.words_length)]
        self.compressed = [self._bits_to_int(word) for word in self.words]
        end = time.perf_counter()
        self._add_timer('compression', f"{end - start:.6f}")

    def uncompress(self, compressed_array: List[int]) -> List[int]:
        start = time.perf_counter()
        # On convertit en bits et on les met à la suite des autres
        self.words = [self._int_to_bits(n, self.words_length) for n in compressed_array]
        phrase = "".join(self.words)
        cursor = self._read_meta(phrase)

        overflow_index_start = (
                cursor +
                (self.total_items * self.best_bit_length) +
                self.total_items
        )
        ints: List[int] = []
        # On retransforme les bits compressés en entiers
        for i in range(self.total_items):
            number_type: str = phrase[cursor:(cursor + 1)]
            cursor += 1
            # On teste si l'entier est un overflow
            if number_type == '1':
                # On récupère la position
                bits: str = phrase[cursor:(cursor + self.best_bit_length)]
                cursor += self.best_bit_length
                position: int = self._bits_to_int(bits)
                # On récupère l'entier dans les overflows grâce à la position
                overflow_position = (overflow_index_start + (position * self.max))
                overflow_bits = phrase[overflow_position:(overflow_position + self.max)]
                ints.append(self._bits_to_int(overflow_bits))
            else:
                # On récupère l'entier
                bits: str = phrase[cursor:(cursor + self.best_bit_length)]
                ints.append(self._bits_to_int(bits))
                cursor += self.best_bit_length
        end = time.perf_counter()
        self._add_timer('decompression', f"{end - start:.6f}")
        return ints

    def get(self, i: int) -> int:
        start = time.perf_counter()
        phrase = "".join(self.words)
        # On place le curseur à l'emplacement de l'entier ou de sa position dans le cas d'un overflow
        cursor = 76 + ((self.best_bit_length + 1) * i)
        bits = phrase[cursor:(cursor + self.best_bit_length + 1)]
        number_type = bits[:1]
        overflow_index_start = (
                76 +
                (self.total_items * self.best_bit_length) +
                self.total_items
        )
        # On teste si l'entier est un overflow
        if number_type == '1':
            position = self._bits_to_int(bits[1:])
            overflow_position = (overflow_index_start + (position * self.max))
            overflow_bits = phrase[overflow_position:(overflow_position + self.max)]
            end = time.perf_counter()
            self._add_timer('reading_int', f"{end - start:.6f}")
            return self._bits_to_int(overflow_bits)
        else:
            end = time.perf_counter()
            self._add_timer('reading_int', f"{end - start:.6f}")
            return self._bits_to_int(bits[1:])

#####
# BitPacker sans "crossing" (les bits des entiers ne sont pas séparés lors du
# passage en mot de 32 bits)
#####
class BitPackerNoCrossing(BaseBitPacker):
    def compress(self):
        if not len(self.array):
            raise "no array has been given, cannot compress"
        start = time.perf_counter()
        # On écrit les métadonnées
        phrase: str = self._write_meta()
        overflow_list = self._get_overflow_list()
        # On écrit dans "suffix" tous les entiers overflow
        suffix = "".join([self._int_to_bits(key, self.max) for key in overflow_list.keys()])

        self.total_overflow = len(overflow_list)
        phrase += self._int_to_bits(self.total_overflow, 32)

        # On écrit soit l'entier, soit la position de l'overflow
        for number in self.array:
            bit_length = number.bit_length()
            if bit_length > 30:
                # On a une limite de 30 car on utilise deux bits comme code :
                # un bit pour indiquer le début d'un entier
                # un bit pour signaler si c'est un entier overflow
                raise ValueError("Integer is larger than 30 bits")
            else:
                available_space = (32 - len(phrase) % 32) % 32
                # On teste si l'entier est un overflow
                if bit_length <= self.best_bit_length:
                    # On teste si l'on doit écrire l'entier dans un nouveau mot
                    if bit_length + 2 > available_space:
                        phrase += "0" * available_space
                    phrase += "10" + self._int_to_bits(number, self.best_bit_length)
                else:
                    if self.total_overflow.bit_length() + 3 > available_space:
                        phrase += "0" * available_space
                    phrase += "11" + self._int_to_bits(overflow_list.get(number), self.best_bit_length)
                    suffix += self._int_to_bits(number, self.max)

        # On ajoute les overflow
        for i in range(0, len(suffix), self.max):
            available_space = (32 - len(phrase) % 32) % 32
            if self.max + 2 > available_space:
                phrase += "0" * available_space
            phrase += "1"
            for y in range(0, self.max):
                phrase += suffix[i + y]

        # On ajoute des "0" à la fin pour que le dernier entier compressé soit correct
        padding_length = (32 - len(phrase) % 32) % 32
        phrase = phrase + ("0" * padding_length)

        self.words = [phrase[i:i + self.words_length] for i in range(0, len(phrase), self.words_length)]
        self.compressed = [self._bits_to_int(word) for word in self.words]
        end = time.perf_counter()
        self._add_timer('compression', f"{end - start:.6f}")

    def uncompress(self, compressed_array: List[int]) -> List[int]:
        start = time.perf_counter()
        # On convertit en bits et on les met à la suite des autres
        self.words = [self._int_to_bits(n, self.words_length) for n in compressed_array]
        phrase = "".join(self.words)
        cursor = self._read_meta(phrase)

        ints: List[int] = []
        proceed = True
        # On retransforme les bits compressés en entiers
        while cursor < len(phrase) and proceed:
            # On récupère le premier bit qui indique si une suite de "0" s'arrête ici
            char: str = phrase[cursor:(cursor + 1)]
            cursor += 1
            
            if char == '1':
                number_type = phrase[cursor:(cursor + 1)]
                cursor += 1

                # On teste si l'entier est un overflow
                if number_type == '1':
                    bits: str = phrase[cursor:(cursor + self.best_bit_length)]
                    position: int = self._bits_to_int(bits)
                    overflow_bits = self._get_overflow(phrase, position)
                    ints.append(self._bits_to_int(overflow_bits))
                else:
                    bits: str = phrase[cursor:(cursor + self.best_bit_length)]
                    ints.append(self._bits_to_int(bits))

                cursor += self.best_bit_length

            if len(ints) == self.total_items:
                proceed = False
        end = time.perf_counter()
        self._add_timer('decompression', f"{end - start:.6f}")
        return ints

    def get(self, i: int) -> int:
        phrase = "".join(self.words)
        cursor = self._read_meta(phrase)
        total_words: int = 0
        while cursor < len(phrase):
            char: str = phrase[cursor:(cursor + 1)]
            cursor += 1
            # On teste jusqu'à trouver le bit qui indique si la suite représente
            # un entier ou une position
            if char == '0':
                continue
            else:
                if total_words < self.total_items:
                    number_type = phrase[cursor:(cursor + 1)]
                    cursor += 1
                    # On teste si l'on est à l'emplacement de l'entier recherché
                    if total_words == i:
                        bits = phrase[cursor:(cursor + self.best_bit_length)]
                        # On teste si l'entier est un overflow
                        if number_type == '1':
                            return self._bits_to_int(
                                self._get_overflow(phrase, self._bits_to_int(bits))
                            )
                        else:
                            return self._bits_to_int(bits)
                    total_words += 1
                    cursor += self.best_bit_length
        raise 'Unable to get number'

    def _get_overflow(self, phrase: str, position: int) -> str:
        start = time.perf_counter()
        cursor: int = (32 * 2) + (self.meta_words_length * 2)
        total_words: int = 0
        total_overflow: int = 0
        while cursor < len(phrase):
            char: str = phrase[cursor:(cursor + 1)]
            cursor += 1
            # On teste jusqu'à trouver le bit qui indique si la suite représente
            # un entier ou une position
            if char == '0':
                continue
            else:
                # On teste si l'on est au niveau des entiers overflow
                if total_words < self.total_items:
                    total_words += 1
                    cursor += self.best_bit_length + 1
                else:
                    # On teste si l'on est à la position de l'overflow
                    if total_overflow == position:
                        end = time.perf_counter()
                        self._add_timer('reading_overflow', f"{end - start:.6f}")
                        return phrase[cursor:(cursor + self.max)]
                    else:
                        total_overflow += 1
                        cursor += self.max
        raise 'Unable to get overflow number'

####
# BitPacker Factory
# - Retourne la class BitPacker correspondant à la méthode choisie
####
def bit_packer_factory(compress_type: str, array: List[int]):
    if compress_type == 'crossing':
        return BitPackerCrossing(array)
    elif compress_type == 'nocrossing':
        return BitPackerNoCrossing(array)
    else:
        raise "Unknown compress type"
