def sents2vectors(token_lines):
    sentence_record = {}
    sentence_vectors = {}

    for line_num, line in enumerate(token_lines):
        info = line.split('\t')
        current_sent_index = len(sentence_vectors)

        if info[0] == 'SENTENCE':
            sent_start, sent_end = int(info[1]), int(info[2])

            for i in range(sent_start, sent_end + 1):
                sentence_record[i] = current_sent_index
            if not info[3] == '\n':
                sentence_vectors[current_sent_index] = {}
                sentence_vectors[current_sent_index]['BOUNDS'] = (sent_start, sent_end)
                sentence_vectors[current_sent_index]['TOKEN_BOUNDS'] = []
                sentence_vectors[current_sent_index]['TOKENS'] = []
                sentence_vectors[current_sent_index]['POS'] = []
                sentence_vectors[current_sent_index]['LABELS'] = []
                sentence_vectors[current_sent_index]['RAW'] = info[3]

        elif info[0] == 'token':
            tok, start, end, pos = info[1], int(info[2]), int(info[3]), info[4].strip()

            sent = sentence_record[start]
            sentence_vectors[sent]['TOKEN_BOUNDS'].append((start, end))
            sentence_vectors[sent]['POS'].append(pos)
            sentence_vectors[sent]['TOKENS'].append(tok.strip())
    return sentence_vectors
