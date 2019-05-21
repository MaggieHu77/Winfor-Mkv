
def printt(content, flag=False):
    """
    use to control whether to print the processing information.

    :param content: string to print.
    :param flag: if True, print; else close print IO not in development process.
    """
    if flag:
        print(content)