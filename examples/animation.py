from furniture.animation import Animation

def draw(frame):
    fill(random(), random(), random())
    rect(*frame.page)

animation = Animation(draw, 60)
animation.storyboard(frames=(0,))