# TV Fixer

I'm making this because I have nearly 200 episodes of a show to go through to make sure they're in the right order, but
I really don't feel like opening each one up by-hand in VLC to verify that it's the correct episode. Furthermore, I
don't particularly feel like doing any kind of dance with file renaming to shuffle the filenames around when I discover
that some episode IS, in fact, out of order.

I would rather spend EVEN MORE time on building a tool to let me rename things and preview certain timecodes to check
the episode title screens and rearrange episodes within the tool and have to tool do all the fancy renaming and
shuffling when I'm done.

And god forbid I make a mistake while renaming and have to go back and RE-FIX all the file names, good grief!

No, thanks, I'd rather just make a tool for that. Cheers.

## Building

Requirements:
- PyQt6
  - `pip install pyqt6`
- [VLC](https://www.videolan.org/vlc/) (installed it on your machine)
  - also `pip install python-vlc`

...and then you're done. It's a Python script, so just run `main.py` for now, and it'll run your stuff.

## Roadmap

(Not like a hard "this will be done" but more like... ideas of things it would be nice to have?)

- [x] Automatically display a frame at a set timestamp (to help with more quickly reading/checking episode names)
- [x] Allow manual renumbering of files and automate renumbering the rest in-order
- [ ] Support handling multiple seasons at once (currently, the renumbering wouldn't reset)
  - [ ] This includes rearranging files into seasons folders
- [ ] Infer show titles and season numbers by scanning parent directories
- [ ] Use TVBD to search for episode titles for you
- [ ] Use OpenCV/OCR to scan for text/titles automatically