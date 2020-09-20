from configparser import ConfigParser

def read_config(filename, section):
    """ Reads a section from a .ini file and returns a dict object
    """

    parser = ConfigParser()
    parser.read(filename)

    dic = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            dic[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return dic
