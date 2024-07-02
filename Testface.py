import cv2

def save_video_section(cap, start_frame, end_frame, output_filename, fourcc, fps, frame_size):
    out = cv2.VideoWriter(output_filename, fourcc, fps, frame_size)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    for frame_num in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    
    out.release()

# Öffne das Video
cap = cv2.VideoCapture('path_to_your_video.mp4')

# Bestimme die Videoeigenschaften
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Berechne die Abschnitte
section_length = total_frames // 4
sections = [(i * section_length, (i + 1) * section_length) for i in range(4)]

# Letzten Abschnitt sicherstellen, dass er bis zum Ende des Videos geht
sections[-1] = (sections[-1][0], total_frames)

# Erstelle den Video-Codec
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec für das Videoformat

# Speichere die Videoabschnitte
save_video_section(cap, sections[0][0], sections[0][1], 'output_part1.mp4', fourcc, fps, (frame_width, frame_height))
save_video_section(cap, sections[1][0], sections[1][1], 'output_part2.mp4', fourcc, fps, (frame_width, frame_height))
save_video_section(cap, sections[2][0], sections[2][1], 'output_part3.mp4', fourcc, fps, (frame_width, frame_height))
save_video_section(cap, sections[3][0], sections[3][1], 'output_part4.mp4', fourcc, fps, (frame_width, frame_height))

# Ressourcen freigeben
cap.release()
cv2.destroyAllWindows()
