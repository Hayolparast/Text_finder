import json
import os
from rapidfuzz import fuzz
import time


# Засекаем время начала выполнения
start_time = time.time()


#Vozvrashaem tekst iz fayla kak stroku
def read_text_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def prepare_words(words):
    original_words = words.copy()
    lower_words = [word.lower() for word in words]
    return original_words, lower_words

def find_best_match_dynamic_window(transcription, original_words, lower_words, delta=3, prev_idx=None):
#Isem sovpadenie s nijnim registorom slov no vozvrashaem original!!!
    num_words = len(transcription.strip().split())
    min_len = max(1, num_words - delta)
    max_len = num_words + delta

    best_score = 0
    best_idx = prev_idx
    best_text = None

    if prev_idx is None:
        start_idx = 0
        end_idx = len(original_words) - 1
    else:
        start_idx = max(0, prev_idx - 3 * num_words)
        end_idx = min(prev_idx + 3 * num_words, len(original_words) - 1)

    lower_transcription = transcription.lower()

    for size in range(min_len, max_len + 1):
        for i in range(start_idx, end_idx - size + 1):
            window = lower_words[i:i + size]
            candidate = ' '.join(window)
            score = fuzz.ratio(lower_transcription, candidate)

            if score > best_score:
                if transcription == "shunda qari ayol mosko gubernatorining qulog'iga uchta to'xtashga tegishli in'omni eshittirgan edi":
                    print("candidate: ", candidate)
                    print("score : ", score)
                best_score = score
                best_idx = i + size
                best_text = ' '.join(original_words[i:i + size])

    return best_text, best_score, best_idx

def process_json_data(data, original_words, lower_words, best_idx=None):
#Obrobotka Json faylov, dobovlyaem naydennie sxojie predlojenie i protsent sxojesti
    for item in data:
        transcription = item.get("transcription")

        if transcription:
            best_text, best_score, best_idx = find_best_match_dynamic_window(
                transcription, original_words, lower_words, prev_idx = best_idx
            )

            if best_score >= 70:
                item["original"] = best_text
                item["similarity_percent"] = best_score
            else:
                item["original"] = None
                item["similarity_percent"] = best_score
                best_idx = None
        else:
            item["original"] = None
            item["similarity_percent"] = None
            best_idx = None

def process_files(json_file, txt_file):
#obrabativaem JSON i text fayli i soxranyaem.)
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    big_text = read_text_from_file(txt_file)
    words = big_text.strip().split()
    original_words, lower_words = prepare_words(words)

    process_json_data(data, original_words, lower_words)

    valid_scores = [item["similarity_percent"] for item in data if item["similarity_percent"] is not None]
    average_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

    output_file = os.path.join(
        os.path.dirname(json_file),
        "updated_" + os.path.basename(json_file)
    )
    
    result = {
        "average_similarity": average_score,
        "data": data
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if average_score is not None:
        print(f"Sredniy protsent sxojesti: {average_score:.2f}%")
    else:
        print("Netu dannix")

    print(f"Soxranili v: {output_file}")

def process_all_folders(root_folder):
#Obrobotka PODpapok v ukazinnoy direktori
    for subfolder in os.listdir(root_folder):
        subfolder_path = os.path.join(root_folder, subfolder)

        if os.path.isdir(subfolder_path):
            json_file = None
            txt_file = None

            for filename in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, filename)

                if filename.endswith('.json'):
                    json_file = file_path
                elif filename.endswith('.txt'):
                    txt_file = file_path

            if json_file and txt_file:
                print(f"\nRabota s papkami: {subfolder}")
                process_files(json_file, txt_file)
            else:
                print(f"V papke {subfolder} Netu JSON ili text")

if __name__ == "__main__":
    root_folder = r'C:\Users\Maniac\Desktop\data_for_alier'
    process_all_folders(root_folder)
    print(f"\nПрограмма выполнена за {time.time() - start_time:.2f} секунд")