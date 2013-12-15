import envoy
import sarge
import re

title_prefix = 'vlcspawn'

def window_number(window_name):
    match = re.search(r'{0}(?P<n>\d+)'.format(title_prefix),
            window_name)
    if match:
        return int(match.groupdict()['n'])

def window_name(window_number):
    return '{prefix}{n}'.format(
                prefix = title_prefix,
                n = window_number
            )

def get_spawned_windows():
    p = envoy.run('wmctrl -l -p -G | grep "{0}"'.format(title_prefix))
    pattern = re.compile(r"""
(?P<handle>[^\s]+)
\s+
(?P<desktop>[^\s]+)
\s+
(?P<pid>[^\s]+)
\s+
(?P<x>\d+)
\s+
(?P<y>\d+)
\s+
(?P<w>\d+)
\s+
(?P<h>\d+)
\s+
(?P<hostname>[^\s]+)
\s+
(?P<name>[^\s]+)
""", re.VERBOSE)
    return [match.groupdict() for match in re.finditer(pattern, p.std_out)]

def get_window_info(name):
    windows = get_spawned_windows()
    return [w for w in windows if w['name'] == name][0]

def next_available_window_number():
    windows = get_spawned_windows()
    window_numbers = [window_number(window['name']) for window in windows]
    if window_numbers:
        return max(window_numbers) + 1
    return 0

def new_vlc(media_file=None, start_time=None, stop_time=None):
    if media_file:
        command = 'vlc "{0}"'.format(media_file)
    else:
        command = 'vlc'
    if start_time:
        command += ' --start-time {0}'.format(start_time)
    if stop_time:
        command += ' --stop-time {0}'.format(stop_time)
    vlc = sarge.run(command, async=True)
    new_name = window_name(next_available_window_number())
    rename = sarge.run('sleep 1 && wmctrl -r "VLC media player" -N "{0}"'.format(
                new_name),
            async=True)
    return new_name

def move_window(name, x, y):
    window = get_window_info(name)
    if window:
        p = envoy.run('wmctrl -r "{name}" -e "1,{x},{y},{w},{h}"'.format(
                name = name,
                x = x,
                y = y,
                w = window['w'],
                h = window['h']
            ))

def resize_window(name, w, h):
    window = get_window_info(name)
    if window:
        p = envoy.run('wmctrl -r "{name}" -e "1,{x},{y},{w},{h}"'.format(
                name = name,
                x = window['x'],
                y = window['y'],
                w = w,
                h = h
            ))

def activate_window(name):
    p = envoy.run('wmctrl -R "{0}"'.format(name))

def media_length(filename):
    p = envoy.run('exiftool "{0}"'.format(filename))
    lines = [line for line in p.std_out.split('\n') if ':' in line]
    info = {line[:line.index(':')].strip(): line[1+line.index(':'):].strip() 
            for line in lines}
    seconds = int(int(info['Video Frame Count']) / float(info['Video Frame Rate']))
    return seconds

def kill_window(name):
    info = get_window_info(name)
    if info:
        p = envoy.run('kill -9 {0}'.format(info['pid']))

def kill_all():
    for window in get_spawned_windows():
        kill_window(window['name'])
