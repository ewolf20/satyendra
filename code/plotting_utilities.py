import matplotlib.pyplot as plt 


def initialize_live_plot(num = None, can_make_interactive = True):
    if(can_make_interactive and not plt.isinteractive()):
        plt.ion() 
    fig = plt.figure(num = num) 
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8]) 
    return (fig, ax) 


def update_live_plot(x, y, fmt = '', ax = None, clear_previous = True, keep_settings = True, pause_length = 0.001, **kwargs):
    if ax == None:
        ax = plt.gca()
    if clear_previous:
        if keep_settings:
            for artist in ax.lines + ax.collections:
                artist.remove()
        else:
            ax.clear() 
    ax.plot(x, y, fmt, **kwargs) 
    plt.draw()
    plt.pause(pause_length)


def update_live_plot_imshow(im_data, ax = None, clear_previous = True, keep_settings = True, pause_length = 0.001, **kwargs):
    if ax == None:
        ax = plt.gca() 
    if clear_previous:
        if keep_settings:
            for image_artist in ax.images:
                image_artist.remove()
        else:
            ax.clear()
    ax.imshow(im_data, **kwargs) 
    plt.draw() 
    plt.pause(pause_length)