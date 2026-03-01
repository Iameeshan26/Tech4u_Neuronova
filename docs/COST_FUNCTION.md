# Delivery Optimizer: Cost Function Documentation

This document provides transparency into how the Neuronova Delivery Optimizer evaluates and selects routes. The goal is to balance efficiency (time and distance) with business priorities.

## Core Formula

The cost of moving between two points ($i$ to $j$) for a specific vehicle is calculated as:

$$Cost_{ij} = (Time_{ij} \times W_{time} + Distance_{ij} \times W_{fuel}) \times M_{vehicle}$$

Where:
- **$Time_{ij}$**: Travel time in seconds (from TomTom API or Haversine fallback).
- **$Distance_{ij}$**: Travel distance in meters.
- **$W_{time}$**: Weight for time (Importance of speed).
- **$W_{fuel}$**: Weight for fuel (Importance of distance/efficiency).
- **$M_{vehicle}$**: Cost multiplier specific to the vehicle profile (e.g., Heavy Truck = 1.5, Scooter = 0.5).

---

## Weight Configuration

Current weights defined in `config.py`:

| Parameter | Value | Description |
| :--- | :--- | :--- |
| `WEIGHT_TIME` | `1.0` | Primary driver. 1 second of travel adds 1 unit to the cost. |
| `WEIGHT_FUEL` | `0.5` | Secondary driver. 1 meter of travel adds 0.5 units to the cost. |
| `WEIGHT_PRIORITY`| `100.0` | Penalty factor for skipping or delaying high-priority stops. |

### Impact of 1.0/0.5 Split
With this split, the optimizer is biased toward **fastest routes** but will avoid significant distance increases unless the time savings are substantial.
Example: A route that is **100 seconds faster** but **300 meters longer** would be preferred ($100 \times 1.0 > 300 \times 0.5$).

---

## Priority & Penalties

High-priority stops use a "Disjunction" penalty to ensure they are visited first or that the optimizer "hurts" significantly for skipping them.

**Penalty Formula:**
$$Penalty = Priority \times 100 \times 100,000$$

- **Normal Priority (1)**: Base penalty of 10M.
- **High Priority (3)**: Base penalty of 30M.

This ensures that the optimizer will almost always prioritize stops with higher assigned priority values in the input data.
