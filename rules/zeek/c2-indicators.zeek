##! C2LAB Zeek helpers.
##! Ensure JSON logs and JA3 are available for the pipeline.
##! Load the community JA3 package (zkg install ja3) before using ja3 fields in ssl.log.

@load policy/tuning/json-logs        # emit JSON logs for easy parsing
# @load ja3                          # uncomment after: zkg install ja3

# Example: tag high-NXDOMAIN hosts at the Zeek layer (optional; primary logic is in Python).
# Left as a hook for Sprint 1-2 if you want Zeek-side pre-aggregation.
