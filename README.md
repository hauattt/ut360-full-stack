# UT360 - Full Stack Recommendation System

**Customer360-VNS Advance Recommendation Platform**

Complete telecom recommendation system with ML-based customer segmentation and modern web interface.

## 🎯 Features

- **Data Pipeline**: 5-phase automated processing (51M+ records → 214K recommendations)
- **ML Segmentation**: K-Means clustering for customer profiling
- **Business Rules**: Intelligent recommendation engine (Fee/Free/Quota)
- **High Performance**: Redis (<10ms) + PostgreSQL storage
- **Modern Web UI**: React + FastAPI with Customer360 profiles

## 📊 Results

- **214,504 recommendations** | **1.26B VND revenue potential**
- **Fee**: 137,644 | **Free**: 46,582 | **Quota**: 30,278

## 🚀 Quick Start

```bash
# Pipeline
cd pipeline && pip3 install pandas numpy scikit-learn && python3 scripts/run_full_pipeline.py

# Backend
cd backend && pip3 install -r requirements.txt && ./start.sh

# Frontend  
cd frontend && npm install && npm start
```

## 📚 Documentation

- **[READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)** - Deployment guide
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All docs
- **[REDIS_POSTGRES_SUMMARY.md](REDIS_POSTGRES_SUMMARY.md)** - Database architecture

**Status:** ✅ Production Ready | **Version:** 1.0.0
