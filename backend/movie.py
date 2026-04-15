from moviepy.editor import VideoFileClip

video = VideoFileClip("0402.mp4")

faster_video = video.speedx(4)

faster_video.write_videofile("fast_0402.mp4")