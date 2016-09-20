COMMENT_CHAR = '#'
OPTION_CHAR =  '='
MULTI_LINE_COMMENT_STR_1 = "'''"
MULTI_LINE_COMMENT_STR_2 = '"""'

#NOTE:
#this config loader has following limitations
#   multiline comment identifier should be the first string seq. in a line to indicate start
#   multiline comment identifier should be the last string seq in a line to indicate end

def load_config(config_path):
    options = {}
    with open(config_path, 'r') as my_config:
        imy_config = iter(my_config)
        for line in imy_config:
            #handle multiline comments
            MULTI_LINE_COMMENT_1_SET = False
            MULTI_LINE_COMMENT_2_SET = False
            if MULTI_LINE_COMMENT_1_SET and not (line.startswith(MULTI_LINE_COMMENT_STR_1) or line.endswith(MULTI_LINE_COMMENT_STR_1)):
                continue
            if MULTI_LINE_COMMENT_2_SET and not (line.startswith(MULTI_LINE_COMMENT_STR_2) or line.endswith(MULTI_LINE_COMMENT_STR_2)):
                continue
            if not MULTI_LINE_COMMENT_2_SET and (line.startswith(MULTI_LINE_COMMENT_STR_1) or line.endswith(MULTI_LINE_COMMENT_STR_1)):
                MULTI_LINE_COMMENT_1_SET = not MULTI_LINE_COMMENT_1_SET
                continue
            if not MULTI_LINE_COMMENT_1_SET and (line.startswith(MULTI_LINE_COMMENT_STR_2) or line.endswith(MULTI_LINE_COMMENT_STR_2)):
                MULTI_LINE_COMMENT_2_SET = not MULTI_LINE_COMMENT_2_SET
                continue

            # First, remove comments:
            if COMMENT_CHAR in line:
                # split on comment char, keep only the part before
                line, comment = line.split(COMMENT_CHAR, 1)
            # Second, find lines with an option=value:
            if OPTION_CHAR in line:
                # split on option char:
                option, value = line.split(OPTION_CHAR, 1)
                # strip spaces
                option = option.strip()
                # strip spaces, new lines and quotes
                value = value.strip(' \'"\n')
                while value.endswith('\\'):
                    value = value.strip(' \'"\n\\') + next(imy_config).strip(' \'"\n')

                # store in dictionary:
                options[option] = value
    return options
