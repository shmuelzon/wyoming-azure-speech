FROM python:3.13-slim-bookworm

COPY dist/*.whl /tmp
RUN pip install /tmp/*.whl

EXPOSE 10300

CMD ["python", "-m", "wyoming_azure_speech"]
