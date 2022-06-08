import matplotlib.pyplot as plt


"""Initializes a live-plot figure

    Creates and returns a new figure on which data can be live-plotted, which 
    displays as a new window.

    Parameters:

    num: int or str, optional. If passed, piped to matplotlib.pyplot.figure as num. Default None 
    can_make_interactive: bool. If true, the initialization function is allowed to turn on interactive mode 
        (which could interfere with other plotting). Default True. 

    Returns:
    (fig, ax)
    figure: A matplotlib.pyplot.Figure instance created by the method 
    ax: A matplotlib.pyplot.Axes instance attached to figure; this is what does the actual plotting
"""

def initialize_live_plot(num = None, can_make_interactive = True):
    if(can_make_interactive and not plt.isinteractive()):
        plt.ion() 
    fig = plt.figure(num = num) 
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    return (fig, ax)




    """Updates a live_plot figure 

    Plots new data to a live-plotting figure object (or to the currently active one).
    Optionally does this in fancy_plot format.

    Parameters:

    x, y, fmt, **kwargs: Identical to those for ax.plot() 
    fancy: If true, applies fancy_plot to the input data, instead of plot
    ax: The Axes object on which the data should be live-plotted. If None, plt.gca() is called. 
    pause_length: The amount of time passed to plt.pause() to allow drawing. Default 0.001.
    clear_previous: Whether to clear the previous curves off of the live plot when a new one is plotted. Default True. 
    keep_settings: Whether axis settings (e.g. log scale, labels, etc.) are kept when the data is cleared. Default True.
"""
def update_live_plot(x, y, fmt = '', ax = None, fancy = False, clear_previous = True, keep_settings = True, pause_length = 0.001, **kwargs):
    if(ax == None):
        ax = plt.gca() 
    if(clear_previous):
        if(keep_settings):
            for artist in ax.lines + ax.collections:
                artist.remove() 
        else:
            ax.clear()
    if(fancy):
        fancy_plot(x, y, fmt = fmt, ax = ax, **kwargs)
    else:
        ax.plot(x, y, fmt, **kwargs) 
    plt.draw()
    plt.pause(pause_length)