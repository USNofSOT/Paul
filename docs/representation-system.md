# Representation Points Guide

Representation points are used to track work done for the **Media** and **Scheduling** departments.

Each member can have:

- Media points
- Scheduling points
- a combined total

Those totals are used for representation badges and for internal department tracking.

## What JEs can use

### `/representation`

Use this JE command to check representation points.

It shows:

- your total representation points
- your Media and Scheduling split
- your current badge
- your recent point history

JEs can also check another member.

## What department staff can use

### `/representationmod`

Use this command to **add or remove** representation points.

It is for updating points only. It is not the history viewer anymore.

When a change is made, the response shows:

- what action was taken
- who made the change
- the member’s new total count

Required fields:

- `target`
- `department`
- either `add` or `remove`
- `reason`

Important rules:

- you cannot add and remove in the same command
- points cannot go below zero
- a reason is required for every change

## Who can manage points

Representation management is based on **SPD department leadership roles**.

### Can open `/representationmod`

- Head of Media
- XO of Media
- Head of Scheduling
- XO of Scheduling
- BOA
- NSC Administrator

### Can add Media points

- Head of Media
- XO of Media
- BOA
- NSC Administrator

### Can add Scheduling points

- Head of Scheduling
- XO of Scheduling
- BOA
- NSC Administrator

### Can remove Media points

- Head of Media
- BOA
- NSC Administrator

### Can remove Scheduling points

- Head of Scheduling
- BOA
- NSC Administrator

## Exporting department data

### `!dumprepmutations`

This command exports representation data as a CSV file for department leadership.

By default, it exports **both departments together in one file**.

You can also optionally filter to:

- `Media`
- `Scheduling`

The CSV includes two sections:

### 1. Point totals

This shows each member’s:

- member ID
- Media points
- Scheduling points
- total representation points

### 2. Mutation history

This shows every logged point change, including:

- record ID
- member ID
- who changed it
- department
- point amount added or removed
- reason
- time of change

Access for this export is limited to:

- Head of Media
- Head of Scheduling
- BOA
- NSC Administrator

## Automatic award check

The bot checks for pending representation awards automatically.

When someone qualifies:

- the bot sends the pending award to the correct department channel
- the correct department leadership is pinged

Department routing works like this:

- if Media points are higher, it goes to Media
- otherwise it goes to Scheduling

If the totals are tied, it defaults to **Scheduling**.

