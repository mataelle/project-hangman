def make_guess(letter, string):
    """Check if letter is in the word"""
    return string.find(letter) > -1

def form_new_word_template(letter, string, template):
    """Return word status"""
    return ''.join(template[i] if string[i]!=letter else string[i]
                   for i in range(len(string)))

def check_if_win(template):
    """Check if word is solved"""
    return template.find('-') < 0


