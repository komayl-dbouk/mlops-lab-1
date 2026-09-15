#question1:

torch, torchvision, scikit-learn, pillow 
are installed 


#question2:


--backend-store-uri: tells MLflow where to store metadata — experiments, runs, parameters, metrics, tags, run status, timestamps. Here it's sqlite:///mlflow.db, so all that structured data goes into a SQLite database file.

--default-artifact-root: tells MLflow where to store artifacts — the actual files a run produces (model files, plots, datasets, checkpoints, etc.). Here it's ./mlruns, a local directory.

Difference between metadata and artifacts: metadata is small, structured, queryable data (numbers, strings, keys/values) that lives in a database/tracking store and powers search/filter/compare in the UI. Artifacts are large, unstructured binary/file blobs (a model pickle, an image, a CSV) that live in file/object storage and are just referenced by path from the metadata — MLflow doesn't try to query inside them.



#question3:


Not git: they're constantly-changing, generated runtime state (binary DB + growing files) — not source, would just bloat history and conflict.

Not dvc: MLflow already versions/tracks experiments and artifacts itself — DVC is for deliberate data/model snapshots, not a tracking store that mutates on every run.



#question4:


When "food11" doesn't exist yet:

Creates a new experiment named "food11" (logged: Experiment with name 'food11' does not exist. Creating a new experiment.), assigned experiment_id = 1



question5:


log_param: logs a single, fixed value for the whole run — hyperparameters/config (e.g. lr, batch_size, model). It's set once and doesn't change during the run; MLflow treats params as immutable (logging the same key twice with a different value errors).

log_metric: logs a value that evolves over the course of the run — things you measure repeatedly as training progresses (e.g. train_loss, val_accuracy each epoch). The same key can be logged many times.

Why step exists only on log_metric: metrics are inherently a time series — you want to plot val_loss across epochs and see the training curve, so each value needs a position (step) to be ordered/plotted against. 



#question6:


For this run that would be mlruns/1/19b06bc59b094f3ab92070dfd348235d/artifacts/model. The MLflow UI shows this exact file://... path at the top of the Artifacts tab.



question7:


more the learning rate is small
more the val accuracy is better



question8:


The dominant pattern is learning rate, not batch size, drives accuracy.
batch_size doesn't show a consistent directional effect — 32 and 64 both appear across the mid-accuracy runs — so it's a much weaker factor here than lr.


question9:


efficient-shark-63 is the best run having val_accuracy with 0.711
48c533f4806746ceb99ede59a1da1570
