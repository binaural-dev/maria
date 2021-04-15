ARG  ODOO_VERSION=14.0
FROM odoo:${ODOO_VERSION}

# RUN echo "$ODOO_VERSION"
# ENV user_odoo = ""
# RUN echo "$user_odoo"
USER root
RUN apt-get update
RUN pip3 install num2words xlwt xlrd openpyxl xlwt pytest-odoo pandas wheel
USER odoo
