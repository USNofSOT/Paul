# Training
The following document outlines the requirements and design for the bots (PAUL's) training system. 
The training system is responsible for tracking the training points and completion of training for targets.

**1. Training Points** (Trainer)
> The points a user has earned for training others. This is used for example for rewards and commendations.

# Files
Following is a list of files that are part of the training system. This excludes generic files like `config.py` and `models.py`.

| Filename                                        | Description                                                                   | Status |
|-------------------------------------------------|-------------------------------------------------------------------------------|--------|
| /data/repository/training_records_repository.py | The main database facade/repository for anything related to training records. | DONE   |
| /cogs/on_message_training.py                    | The on_message event listener for training points.                            | DONE   |
| /cogs/on_delete_training.py                     | The on_delete event listener for training points.                             | DONE   |
| /cogs/on_member_update_training.py              | The on_member_update event listener for trained completion.                   | DONE   |
| /cogs/populate_training_records.py              | The populate_training_records command.                                        | DONE   |
| /cogs/training_records.py                       | The training_records command.                                                 | DONE   |
| /utils/training_utils.py                        | The utility functions for training records                                    | DONE   |

# Abbreviations
The following abbreviations are used in this document:
- USN: United States Navy of SOT
- NRC: New Recruit Command
- NETC: Naval Education and Training Command
- JLA: Junior Leadership Academy
- SNLA: Senior non-commissioned officer
- OCS: Officer Candidate School
- SOCS: Senior Officer Candidate School

# Considerations
There should be someway for a user to check their training points. 
So they know if everything is being added correctly. And they can alert us if something is wrong.

# Datamodel: training_records
| Field                 | Description                                                               | Type     | Optional | Default | Context |
|-----------------------|---------------------------------------------------------------------------|----------|----------|---------|---------|
| target_id (`PK`/`FK`) | The discord ID of the target                                              | BIGINT   | FALSE    |         |         |
| NRC_training_points   | The number of New Recruit Command (NRC) trained points                    | INT      | FALSE    | 0       | Trainer |
| NETC_training_points  | The number of Naval Education and Training Command (NETC) trained points. | INT      | FALSE    | 0       | Trainer |
| JLA_training_points   | The number of Junior Leadership Academy (JLA) trained points              | INT      | FALSE    | 0       | Trainer |
| SNLA_training_points  | The number of Senior non-commissioned officer (SNLA) trained points       | INT      | FALSE    | 0       | Trainer |
| OCS_training_points   | The number of Officer Candidate School (OCS) trained points               | INT      | FALSE    | 0       | Trainer |
| SOCS_training_points  | The number of Senior Officer Candidate School (SOCS) trained points       | INT      | FALSE    | 0       | Trainer |
| NLA_training_points   | The number of NLA points (no longer in user) - legacy                     | INT      | FALSE    | 0       | Trainer |
| VLA_training_points   | The number of VLA points (no longer in user) - legacy                     | INT      | FALSE    | 0       | Trainer |


> NETC points are a combination of JLA, SNLA, OCS, and SOCS points.
> NRC points are separate from NETC points.

## training
| Field             | Description                                                            | Type     | Optional | Default | Context |
|-------------------|------------------------------------------------------------------------|----------|----------|---------|---------|
| log_id (`PK`)     | The unique ID of the log entry                                         | BIGINT   | FALSE    |         |         |
| target_id (`FK`)  | The discord ID of the target                                           | BIGINT   | FALSE    |         |         |
| log_channel_id    | The discord ID of the channel where the log entry was made             | BIGINT   | FALSE    |         |         |
| training_type     | The type of training that was logged (NRC, NETC, JLA, SNLA, OCS, SOCS) | ENUM     | FALSE    |         |         |
| training_category | The category of training that was logged (NRC, NETC)                   | ENUM     | FALSE    |         |         |
| log_time          | The time of the log entry                                              | DATETIME | FALSE    |         |         |


```mermaid
erDiagram
    TrainingRecord {
        BIGINT target_id
        INT nrc_training_points
        INT netc_training_points
        INT jla_training_points
        INT snla_training_points
        INT ocs_training_points
        INT socs_training_points
        INT nla_training_points
        INT vla_training_points
    }
    
    Training {
        BIGINT log_id
        BIGINT target_id
        BIGINT log_channel_id
        ENUM training_type
        ENUM training_category
        DATETIME log_time
    }

    Sailor {
        BIGINT sailor_id
        STRING name
        DATE enlisted_date
    }
    
    TrainingRecord o|--|| Sailor : "has a"
    Training o|--|| Sailor : "has a"
```

# Adding training points
To add training points to a target, the bot will watch for message in certain channels. When a message is detected, the bot will add training points to the target. 
```mermaid
sequenceDiagram
    participant S as Sailor (Target)
    participant L as USN @ training-log
    participant B as Bot
    participant DB as Database
        
    B-->L: listen for message
    S->>L: message
    B->>DB: get_or_create_target
    DB-->>B: target: Training
    B->>DB: increment_nrc_trained_points
    DB-->>B: target: Training

    
    S->>L: remove message
    B->>DB: get_or_create_target
    DB-->>B: target: Training
    B->>DB: decrement_nrc_trained_points
    DB-->>B: target: Training
```

We have 2 type of points to worry about 

| Type | Description                                                                                                                                                 |
|------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| NRC  | New Recruit Command (NRC) training points. This is the basic training given for training new recruits.                                                      |
| NETC | Naval Education and Training Command (NETC) training points. This is the advanced training given. This may include several categories of training.          |