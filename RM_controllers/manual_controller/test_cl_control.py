import sys
sys.path.append('/home/simonhwk/RobotMetabolism/particleTrussServer')

import threading
import time
import RM_Retinas.main as retinas  # Assuming retinas.py is in the same directory

# Function to run the retinas thread
def run_retinas():
    retinas.retinas_thread()

# Create and start the retinas thread as a daemon
retinas_thread = threading.Thread(target=run_retinas, daemon=True)
retinas_thread.start()

# Main script loop to periodically print the retinas data
try:
    while True:
        if hasattr(retinas, 'retinas_data'):
            print("Retinas Data:", retinas.retinas_data)
        else:
            print("Retinas data not available yet.")
        time.sleep(5)  # Wait for 5 seconds before printing again
except KeyboardInterrupt:
    print("Stopping main script.")


# example data output:
# Retinas Data: {14: {'centroid': (0.07075065509265721, -0.25456650387591034, -0.006115126794151505), 'upper_tip': (0.0661878744825622, -0.12189110264311516, -0.006363823172106285), 'bottom_tip': (0.0739161034182324, -0.3872434322078592, -0.005942559671453702)}, 27: {'centroid': (-0.039358557112312426, -0.3067775513973511, -0.007710847828674004), 'upper_tip': (-0.14441187533361854, -0.22561379025196532, -0.004528841218400862), 'bottom_tip': (0.06256502012369594, -0.38719045751225095, -0.029468024342761343)}, 28: {'centroid': (-0.05971829872306564, -0.15776486656692912, 0.00017834033160955427), 'upper_tip': (0.06682388485606405, -0.11963764268972249, -0.012150906144081696), 'bottom_tip': (-0.18591261856793334, -0.1950202811738458, -0.0019136376144052929}})