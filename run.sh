#!/bin/bash

# uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
uvicorn app.server:sio_app  --reload --host 0.0.0.0 --port 8000