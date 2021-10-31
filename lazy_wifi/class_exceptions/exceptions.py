
class LazyWifiException(Exception):
    def __init__(self):
        pass


class ConfigurationException(Exception):
    """
        Exception raised when an invalid element was specified in the config file
    """

    def __init__(self, section=None, message=None, special_exception=None):

        if special_exception:
            self.message = f"Config section {section}\n" \
                           f"Message: {message} \n " \
                           f"Additional Exception: {special_exception}"
        else:
            self.message = f"Config section {section}\n" \
                           f"Message: {message}\n"

    def __str__(self):
        return self.message

