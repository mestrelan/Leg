import os
import pathlib
import json
import whisper
import subprocess

# --- CONFIGURAÇÕES ESPECÍFICAS PARA MÚSICA EM ESPANHOL ---

# Use 'large' para melhor qualidade em letras de música.
WHISPER_MODEL = whisper.load_model("large") 

# --- FORÇAR ESPANHOL ---
# 'es' é o código para Espanhol.
FORCAR_IDIOMA = 'es'

# --- PROMPT DE MÚSICA ---
# O prompt em Espanhol ajuda ainda mais o modelo a "entrar no clima".
# Dizemos que é uma letra de música (Lyrics) para ele formatar melhor.
PROMPT_INICIAL = "La letra de una canción cristiana o música pop. Transcripción lírica precisa, verso por verso."

PROCESSED_LOG_FILE = "videos_processados.json"
OUTPUT_FOLDER_NAME = "videos_legendados"
Pasta_para_processar = 'Alabanzas baixando' # <-- Verifique se o nome da pasta está correto

# ---------------------

def _carregar_log_processados(log_path):
    if log_path.exists():
        with open(log_path, 'r') as f:
            return json.load(f)
    return {}

def _salvar_log_processados(log_path, log_data):
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=4)

def criar_arquivo_srt(segments, srt_path):
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments):
            start = seg['start']
            end = seg['end']
            text = seg['text'].strip()

            def format_time(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t * 1000) % 1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"

            f.write(f"{i + 1}\n")
            f.write(f"{format_time(start)} --> {format_time(end)}\n")
            f.write(f"{text}\n\n")

def gravar_legenda_com_ffmpeg(input_video_path, srt_path, output_video_path):
    """
    Grava a legenda usando libx264.
    """
    # Mantive a fonte grande e contraste alto.
    style = "Fontname=Arial,FontSize=40,PrimaryColour=&H00FFFFFF,Outline=3,OutlineColour=&H44000000,BackColour=&HAA000000,Alignment=2"
    
    input_path_str = str(input_video_path.resolve())
    output_path_str = str(output_video_path.resolve())
    
    vf_filter = f"subtitles='{srt_path.name}':force_style='{style}',format=yuv420p"
    
    command = [
        'ffmpeg',
        '-i', f'"{input_path_str}"',
        '-vf', f'"{vf_filter}"',
        '-c:v', 'libx264',       
        '-preset', 'fast',       
        '-crf', '23',            
        '-c:a', 'copy',          
        '-y', 
        f'"{output_path_str}"'
    ]
    
    command_str = " ".join(command)
    
    print("Executando FFmpeg...")
    subprocess.run(command_str, check=True, shell=True, cwd=str(input_video_path.parent.resolve()))


def processar_video_ffmpeg(video_path: pathlib.Path, log_data: dict, output_dir: pathlib.Path):
    print(f"--- Processando: {video_path.name} ---")

    print(f"Iniciando Transcrição (Forçando idioma: {FORCAR_IDIOMA})...")
    
    transcribe_options = {
        "verbose": False,
        "beam_size": 5,       
        "best_of": 5,
        "patience": 1.0,
        "initial_prompt": PROMPT_INICIAL, # Prompt ajustado para música
        "language": FORCAR_IDIOMA,        # Força Espanhol
        
        # DICA PARA MÚSICA:
        # Se o modelo começar a "alucinar" (repetir frases em partes instrumentais),
        # descomente a linha abaixo:
        # "condition_on_previous_text": False
    }
    
    result = WHISPER_MODEL.transcribe(str(video_path), **transcribe_options)
    
    segments = result.get('segments', [])
    detected_language = result.get('language', 'desconhecido')
    
    # Mesmo forçando, o Whisper retorna o que ele detectou. Deve ser 'es'.
    print(f"Idioma Detectado/Usado: {detected_language} | Segmentos: {len(segments)}")

    if not segments:
        print("❌ AVISO: Nenhuma fala detectada. Pulando vídeo.")
        return

    srt_path = video_path.with_suffix('.srt')
    criar_arquivo_srt(segments, srt_path)
    print(f"SRT criado: {srt_path.name}")
    
    output_filename = output_dir / f"{video_path.stem}_legendado.mp4"
    
    try:
        gravar_legenda_com_ffmpeg(video_path, srt_path, output_filename)
        
        log_data[video_path.name] = {
            "status": "PROCESSADO",
            "idioma": detected_language,
            "caminho_saida": str(output_filename),
            "data_processamento": os.stat(video_path).st_mtime
        }
        print(f"✅ Sucesso: {video_path.name}\n")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO FFmpeg: {e}")
    finally:
        if srt_path.exists():
            os.remove(srt_path)

def main(folder):
    input_path_str = folder
    input_dir = pathlib.Path(input_path_str)
    
    if not input_dir.is_dir():
        print(f"Erro: Pasta não encontrada: '{input_path_str}'")
        return

    output_dir = input_dir / OUTPUT_FOLDER_NAME
    output_dir.mkdir(exist_ok=True)
    print(f"Saída: {output_dir}")

    log_path = input_dir / PROCESSED_LOG_FILE
    log_data = _carregar_log_processados(log_path)
    
    extensions = ['*.mp4', '*.MP4', '*.mkv', '*.MKV', '*.avi', '*.mov']
    videos_to_process = []
    for ext in extensions:
        videos_to_process.extend(input_dir.glob(ext))

    if not videos_to_process:
        print("Nenhum vídeo encontrado.")
        return
        
    for video_path in videos_to_process:
        file_name = video_path.name
        if file_name.startswith("~$") or file_name.startswith("._"):
            continue

        current_mtime = os.stat(video_path).st_mtime

        if file_name in log_data:
            logged_mtime = log_data[file_name].get("data_processamento")
            if logged_mtime == current_mtime:
                print(f"Skipping: {file_name} (Já processado).")
                continue

        processar_video_ffmpeg(video_path, log_data, output_dir)
        _salvar_log_processados(log_path, log_data)
        
    print("\n✅ Fim do processamento.")

if __name__ == "__main__":
    main(Pasta_para_processar)