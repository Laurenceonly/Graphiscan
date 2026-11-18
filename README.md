# GraphiScan

GraphiScan is a capstone project exploring image classification as an aid to screening handwriting for possible dysgraphia-related difficulties. Its results are preliminary screening outputs, not clinical diagnoses, and require expert review.

Teachers can manage student records and submit handwriting samples. Authorized experts can review results, and parents can access information according to their permissions. A separate administrator interface supports account and record management.

## Applications and technology

| Component | Location | Technology |
| --- | --- | --- |
| Mobile app | [graphiscan/mobile-app](graphiscan/mobile-app/) | React Native and Expo |
| Admin interface | [graphiscan/admin-web](graphiscan/admin-web/) | Vue 3 |
| API and inference | [graphiscan](graphiscan/) | Python, Flask and LiteRT |
| Landing site | [graphiscan/landing-web](graphiscan/landing-web/) | Web frontend |
| Data and identity | [graphiscan/db](graphiscan/db/) | Supabase Auth, PostgreSQL and private Storage |

The repository also retains a legacy Flask/MySQL and Vue prototype in `graphiscan/user-app`. Model training uses TensorFlow/Keras; deployed model binaries and private configuration are supplied separately.

## Project status

Android version 1.0.5 was published on 13 November 2026. The system uses the labels **Normal** and **High Potential**. As last verified on that date, ResNet50 was the default selectable model. Physical-device and authenticated end-to-end acceptance checks remain incomplete; see [KNOWLEDGE.md](KNOWLEDGE.md) and [CHANGELOG.md](CHANGELOG.md) for dated evidence and limitations.

## Getting started

Component-specific instructions are in the [mobile app](graphiscan/mobile-app/README.md), [admin web](graphiscan/admin-web/README.md), [landing site](graphiscan/landing-web/README.md), and [API documentation](graphiscan/api/README.md). Some component notes contain historical checkpoints; consult the latest entries in `KNOWLEDGE.md` before applying migrations or deployment instructions. Local Python environments may need to be recreated as described there.

Use the provided example configuration files as templates. Obtain real configuration, model artifacts, and access through the project maintainers; never commit credentials, signing keys, student records, or handwriting samples.

## Documentation

- [System flow](SYSTEM_FLOW.md) and [system map](KNOWLEDGE.md)
- [API contract](API_CONTRACT.md) and [database notes](graphiscan/db/MIGRATION_NOTES.md)
- [Project plan](PROJECT_PLAN.md), [handoff notes](RESUME.md), and [changelog](CHANGELOG.md)
- [Manuscript and defense reviews](docs/manuscript/README.md)

Student records and handwriting images require restricted access. Model scores must be interpreted as screening outputs and reviewed by an authorized expert.
