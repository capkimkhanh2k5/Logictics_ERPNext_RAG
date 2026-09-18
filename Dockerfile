FROM frappe/erpnext:v15

USER frappe

# Copy the custom app
COPY --chown=frappe:frappe apps/logistics_wizard /home/frappe/frappe-bench/apps/logistics_wizard

# Install the app in the python virtual environment
RUN cd /home/frappe/frappe-bench && \
    ./env/bin/pip install -q -U -e ./apps/logistics_wizard

# Add to apps.txt so Frappe knows it's installed
RUN echo "" >> /home/frappe/frappe-bench/sites/apps.txt && \
    echo "logistics_wizard" >> /home/frappe/frappe-bench/sites/apps.txt

# Build assets
RUN cd /home/frappe/frappe-bench && \
    bench build && rm -rf /home/frappe/frappe-bench/assets && cp -R /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets
