# GraphiScan

GraphiScan is a capstone project that explores how image classification can support handwriting screening for possible dysgraphia-related difficulties. It is designed as a **screening aid**, with expert review of results, and is not a clinical diagnosis.

## Project overview

Teachers can manage student records and submit handwriting samples for screening. The application records the model result, supports expert validation, and presents reviewed information to authorized users. A separate admin interface supports account and record management.

## Built with

- **Application:** Flask API and Vue 3 interfaces built with Vite.
- **Machine learning:** TensorFlow/Keras and image preprocessing in Python.
- **Data:** MySQL in the current prototype, with a PostgreSQL migration planned.
- **Mobile direction:** A Vue app with Capacitor configuration.

## Current status

GraphiScan is in active development. The repository contains application source and development documentation. A public demo link will be added after deployment.

## Responsible use

Model scores are screening outputs, not medical conclusions. A qualified expert should review results before they are shared. Student records and handwriting images require restricted access and must not be placed in a public repository or public storage bucket.
