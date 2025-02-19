import re
import numpy as np

class Dialogue:

    def __init__(self):
        self.voc_arr = []
        self.voc_size = 0
        self.voc_dict = {}
        self.seq_data = []
        self.input_max_len = 0
        self.output_max_len = 0

        self.index_in_epoch = 0

    def load_data(self, path):
        data = np.load(path)
        for line in data:
            self.seq_data.append(line)

    # 문자열로 바꾸어준다.
    def decode(self, indices, string=False):
        tokens = [[self.voc_arr[i] for i in dec] for dec in indices]

        if string:
            return self._decode_to_string(tokens[0])
        else:
            return tokens

    def _decode_to_string(self, tokens):
        text = ' '.join(tokens)
        return text.strip()

    # E 가 있는 전까지 반환
    def cut_eos(self, indices):
        eos_idx = indices.index('_E_')
        return indices[:eos_idx]

    # E 인지 아닌지 검사
    def is_eos(self, voc_id):
        return voc_id == 2

    # 정규화식에서 빼고 띄워쓰기 기준으로 자른다.
    def tokenizer(self, sentence):
        sentence = re.sub("[.,!?\"':;)(]", ' ', sentence)
        tokens = sentence.split()
        return tokens

    def tokens_to_ids(self, tokens):
        ids = [self.voc_dict[token] if token in self.voc_arr else self.voc_dict['_U_'] for token in tokens]
        return ids

    # id를 토큰으로 바꿔 반환한다.
    def ids_to_tokens(self, ids):
        tokens = [self.voc_arr[id] for id in ids]
        return tokens

    # max_len 만큼 패딩 추가.
    def pad(self, seq, max_len, start=None, eos=None):
        if start:
            padded_seq = [1] + seq  # 1은 시작 심볼
        elif eos:
            padded_seq = seq + [2]  # 2는 끝 심볼
        else:
            padded_seq = seq

        if len(padded_seq) < max_len:
            return padded_seq + ([0] * (max_len - len(padded_seq))) # 0은 패딩 심볼
        else:
            return padded_seq

    # batct_size만큼 입력데이터를 반환
    def next_batch(self, batch_size):
        enc_batch = []
        dec_batch = []
        target_batch = []
        enc_length = []
        dec_length = []

        start = self.index_in_epoch

        if self.index_in_epoch + batch_size < len(self.seq_data) - 1:
            self.index_in_epoch = self.index_in_epoch + batch_size
        else:
            self.index_in_epoch = 0

        batch_set = self.seq_data[start:start + batch_size]


        for i in range(0, len(batch_set) - 1):
            enc_input = batch_set[i]
            if len(batch_set[i]) > 25:
                enc_input = batch_set[i][0:25]
            dec_input = batch_set[i + 1]
            if len(batch_set[i + 1]) > 24:
                dec_input = batch_set[i + 1][0:24]

            enc, dec, tar = self.transform(enc_input, dec_input, 25, 25)

            enc_batch.append(enc)
            dec_batch.append(dec)
            target_batch.append(tar)
            enc_length.append(len(enc_input))
            dec_length.append(len(dec_input)+1)

        return enc_batch, enc_length, dec_batch, dec_length, target_batch

    # 입력과 출력을 변환
    def transform(self, input, output, max_len_input, max_len_output):

        # 각각의 길이만큼 심볼 추가
        enc_input = self.pad(input, max_len_input)
        dec_input = self.pad(output, max_len_output, start=True)
        target = self.pad(output, max_len_output, eos=True)

        return enc_input, dec_input, target

    def load_vocab(self, vocab_path):
        self.voc_arr = []

        with open(vocab_path, 'r', encoding='utf-8') as vocab_file:
            for line in vocab_file:
                self.voc_arr.append(line.strip())

        self.voc_dict = {n: i for i, n in enumerate(self.voc_arr)}
        self.voc_size = len(self.voc_arr)