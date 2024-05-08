import cv2
import argparse
import logging
import os

def extract_frames(video_path, img_path, img_type='jpg'):
    video_cap = cv2.VideoCapture(video_path)
    video_name = video_path.split('.')[0]
   
    frame_idx = 0

    while True:
        ret, frame = video_cap.read()

        if not ret:
            break

        img_name = video_name + "_" + str(frame_idx).zfill(3) + ".jpg"
        logging.info(f"Writing: {img_name}")
        status = cv2.imwrite(f'{img_name}', frame)
        logging.info(f'Image write status: {status}')
        frame_idx += 1

    video_cap.release()

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to the video file', type=str, default='')
    parser.add_argument('-o', '--output', help='Path to the output files', type=str, default='imgs')
    args = parser.parse_args()

    logging.info(f"Opening video: {args.input}")
    logging.info(f"Writing images to: {args.output}")

    extract_frames(args.input, args.output)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
