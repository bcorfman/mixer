import sip
# The sip module must be used to select the v2 versions of these PyQT classes before any other PyQt imports are done.
# Importing the PyQt classes without the sip calls will end up mixing v1 and v2 versions of the APIs and causing errors.
# See https://github.com/ipython/ipython/issues/276. This may be a holdover from my original Python 2.x code, but
# I'm leaving it here since it doesn't hurt anything, and I don't want to have to re-test things at this point.
sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
