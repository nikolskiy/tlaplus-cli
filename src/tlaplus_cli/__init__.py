import truststore

# Inject truststore as early as possible so that all standard library
# and third-party tools relying on `ssl` (such as `requests` and `urllib3`)
# utilize the native OS trust store.
truststore.inject_into_ssl()
