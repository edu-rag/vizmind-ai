# Diagram Sistem Umum: AI-Powered Concept Map Visual Synthesizer (CMVS)

Dokumen ini berisi diagram-diagram tingkat tinggi (high-level) yang menggambarkan arsitektur dan alur kerja sistem CMVS dari perspektif umum, mencakup interaksi antara pengguna, frontend, dan backend.

---

## 1. Activity Diagram (PlantUML)

**Deskripsi:** Activity Diagram ini menggambarkan alur kerja (workflow) lengkap dari sistem CMVS, mulai dari pengguna login hingga mendapatkan peta konsep yang dapat diinteraksikan. Diagram ini menunjukkan aktivitas sequential dan decision points dalam proses.

### 1.1 Activity Diagram (Complete)
```plantuml
@startuml
!theme plain
start

:Pengguna mengakses aplikasi;
:Tampilkan halaman login;

if (Pengguna sudah login?) then (ya)
  :Redirect ke dashboard;
else (tidak)
  :Tampilkan Google OAuth;
  :Pengguna login dengan Google;
  
  if (Autentikasi berhasil?) then (ya)
    :Buat/update session pengguna;
    :Redirect ke dashboard;
  else (tidak)
    :Tampilkan error message;
    stop
  endif
endif

:Tampilkan dashboard dengan upload zone;
:Pengguna pilih file PDF;

if (File valid?) then (ya)
  :Upload file ke server;
  :Tampilkan loading indicator;
  
  :Ekstraksi teks dari PDF;
  
  if (Ekstraksi berhasil?) then (ya)
    :Proses teks dengan AI untuk generate konsep;
    
    if (Generate konsep berhasil?) then (ya)
      :Simpan peta konsep ke database;
      :Return data peta konsep ke frontend;
      :Tampilkan visualisasi peta konsep;
      
      :Pengguna berinteraksi dengan peta konsep;
      
      if (Pengguna pilih node?) then (ya)
        :Tampilkan detail node;
        
        if (Pengguna bertanya tentang node?) then (ya)
          :Proses pertanyaan dengan RAG;
          :Tampilkan jawaban AI;
        endif
      endif
      
      :Simpan ke riwayat;
      
    else (tidak)
      :Tampilkan error AI processing;
      stop
    endif
  else (tidak)
    :Tampilkan error ekstraksi;
    stop
  endif
else (tidak)
  :Tampilkan error validasi file;
  stop
endif

stop
@enduml
```

### 1.2 Activity Diagram (Simplified)
```plantuml
@startuml
!theme plain
start

:Pengguna akses aplikasi;
:Tampilkan login;

if (Sudah login?) then (ya)
  :Ke dashboard;
else
  :Login dengan Google;
  if (Login berhasil?) then (ya)
    :Buat/update session;
    :Ke dashboard;
  else
    :Tampilkan error;
    stop
  endif
endif

:Upload PDF;
if (File valid?) then (ya)
  :Ekstrak teks;
  if (Ekstraksi berhasil?) then (ya)
    :Generate peta konsep;
    if (Berhasil?) then (ya)
      :Simpan & tampilkan peta;
      :Interaksi dengan node;
      if (Tanya tentang node?) then (ya)
        :Jawab dengan AI;
      endif
      :Simpan ke riwayat;
    else
      :Error generate;
      stop
    endif
  else
    :Error ekstraksi;
    stop
  endif
else
  :Error file;
  stop
endif

stop
@enduml
```

---

## 2. Use Case Diagram (Mermaid)

**Deskripsi:** Diagram Use Case ini menggambarkan fungsionalitas utama yang dapat dilakukan oleh pengguna pada sistem CMVS. Diagram ini menunjukkan interaksi antara aktor (Pengguna) dengan sistem secara komprehensif.

```mermaid
graph TD
    Pengguna[Pengguna]

    subgraph "Sistem CMVS"
        UC1[Login dengan Google OAuth]
        UC2[Upload Dokumen PDF]
        UC3[Generate Peta Konsep dengan AI]
        UC4[Interaksi dengan Peta Konsep]
        UC5[Tanya Jawab AI per Node]
        UC6[Kelola Riwayat Peta Konsep]
    end

    Pengguna --> UC1
    Pengguna --> UC2
    Pengguna --> UC4
    Pengguna --> UC5
    Pengguna --> UC6
    UC2 -.-> UC3
    UC4 -.-> UC5
```

---

## 2. Class Diagram

**Deskripsi:** Class Diagram ini menyajikan komponen-komponen utama dalam sistem CMVS. Diagram ini menampilkan entitas kunci di frontend dan backend serta relasi dasarnya untuk memberikan gambaran struktur sistem secara umum.

### 2.1 Class Diagram (Mermaid)
```mermaid
classDiagram
    class Frontend {
        +ConceptMapDisplay
        +NodeDetailPanel
        +FileUploadZone
        +HistorySidebar
        +AuthProvider
        +handleUserInteraction()
    }

    class Backend {
        +AuthService
        +DocumentService
        +ConceptMapService
        +ChatService
        +processRequest()
    }

    class AIEngine {
        +extractTextFromPDF()
        +generateConceptMap()
        +answerQuestion()
        +processRAG()
    }

    class Database {
        +Users
        +Documents
        +ConceptMaps
        +ChatHistory
        +saveData()
        +retrieveData()
    }

    Frontend "1" -- "1" Backend : API Communication
    Backend "1" -- "1" AIEngine : Menggunakan
    Backend "1" -- "1" Database : Akses Data
```

### 2.2 Class Diagram (PlantUML)
```plantuml
@startuml
!theme plain
skinparam classAttributeIconSize 0

class Frontend {
    +ConceptMapDisplay
    +NodeDetailPanel
    +FileUploadZone
    +HistorySidebar
    +AuthProvider
    --
    +handleUserInteraction()
}

class Backend {
    +AuthService
    +DocumentService
    +ConceptMapService
    +ChatService
    --
    +processRequest()
}

class AIEngine {
    +extractTextFromPDF()
    +generateConceptMap()
    +answerQuestion()
    +processRAG()
}

class Database {
    +Users
    +Documents
    +ConceptMaps
    +ChatHistory
    --
    +saveData()
    +retrieveData()
}

class CloudflareR2 {
    +uploadFile()
    +downloadFile()
    +deleteFile()
    +generatePresignedUrl()
}

Frontend -- Backend : API Communication
Backend -- AIEngine : uses
Backend -- Database : accesses
Backend -- CloudflareR2 : stores/retrieves files

@enduml
```

---

## 3. Sequence Diagram

**Deskripsi:** Sequence Diagram ini mengilustrasikan alur interaksi antar komponen sistem untuk skenario utama yaitu proses upload dokumen hingga peta konsep ditampilkan. Diagram ini menunjukkan urutan kejadian dan komunikasi antar komponen.

### 3.1 Sequence Diagram (Mermaid)
```mermaid
sequenceDiagram
    participant U as Pengguna
    participant F as Frontend
    participant B as Backend
    participant AI as AI Engine
    participant DB as Database

    U->>F: Login dengan Google OAuth
    F->>B: Verifikasi token user
    B-->>F: Konfirmasi autentikasi
    
    U->>F: Upload dokumen PDF
    F->>B: Kirim file untuk diproses
    B->>AI: Request ekstraksi teks & generate konsep
    AI-->>B: Return data peta konsep (nodes, edges)
    B->>DB: Simpan peta konsep & metadata
    DB-->>B: Konfirmasi penyimpanan
    B-->>F: Kirim data peta konsep
    F-->>U: Tampilkan visualisasi peta konsep interaktif
```

### 3.2 Sequence Diagram (PlantUML)

```plantuml
@startuml
!theme plain

actor U as "Pengguna"
participant F as "Frontend"
participant B as "Backend"
participant AI as "AI Engine"
database DB as "Database"

U ->> F : Login dengan Google OAuth
F ->> B : Verifikasi token user
B -->> F : Konfirmasi autentikasi

U ->> F : Upload dokumen PDF
F ->> B : Kirim file untuk diproses
B ->> AI : Ekstraksi teks & generate konsep
AI -->> B : Data peta konsep (nodes, edges)
B ->> DB : Simpan peta konsep & metadata
DB -->> B : Konfirmasi penyimpanan
B -->> F : Kirim data peta konsep
F -->> U : Tampilkan visualisasi peta konsep
@enduml
```

---

## 4. Use Case Diagram (PlantUML)

**Deskripsi:** Use Case Diagram dalam format PlantUML ini menggambarkan interaksi antara aktor utama (Pengguna) dengan sistem CMVS. Diagram ini mencakup semua use case utama dengan perspektif yang sama seperti diagram Mermaid di atas, menunjukkan fungsi-fungsi inti sistem secara komprehensif.

```plantuml
@startuml
!theme plain
left to right direction

' Aktor
actor "Pengguna" as User

' Sistem boundary
rectangle "Sistem" {
  
  ' Package untuk grouping use cases
  package "Autentikasi" {
    usecase "Login dengan\nGoogle OAuth" as UC1
    usecase "Mengelola Session\nPengguna" as UC2
    usecase "Logout" as UC14
  }
  
  package "Manajemen Dokumen" {
    usecase "Upload Dokumen PDF" as UC3
    usecase "Validasi File PDF" as UC4
    usecase "Ekstraksi Teks\ndari PDF" as UC5
  }
  
  package "AI & Peta Konsep" {
    usecase "Generate Peta Konsep\ndengan AI" as UC6
    usecase "Visualisasi Peta Konsep\nInteraktif" as UC7
  }
  
  package "Interaksi Peta Konsep" {
    usecase "Interaksi dengan\nPeta Konsep" as UC8
    usecase "Pilih dan Lihat\nDetail Node" as UC9
    usecase "Tanya Jawab AI\nper Node (RAG)" as UC10
  }
  
  package "Manajemen Riwayat" {
    usecase "Simpan Riwayat\nPeta Konsep" as UC11
    usecase "Kelola Riwayat\nPeta Konsep" as UC12
    usecase "Load Peta Konsep\ndari Riwayat" as UC13
  }
}

' Koneksi User dengan Use Cases (primary use cases)
User --> UC1 : "melakukan"
User --> UC3 : "mengunggah"
User --> UC8 : "berinteraksi"
User --> UC12 : "mengelola"
User --> UC13 : "memuat ulang"
User --> UC14 : "keluar"

' Include relationships (base use case includes another)
UC1 .> UC2 : <<include>>
UC3 .> UC4 : <<include>>
UC4 .> UC5 : <<include>>
UC5 .> UC6 : <<include>>
UC6 .> UC7 : <<include>>
UC7 .> UC11 : <<include>>

' Extend relationships (extending use case extends base)
UC9 .> UC8 : <<extend>>
UC10 .> UC9 : <<extend>>

' Additional dependencies
UC13 --> UC7 : "memuat"

@enduml
```

**Penjelasan Use Cases:**

1. **Login dengan Google OAuth** - Pengguna melakukan autentikasi menggunakan akun Google untuk mengakses sistem
2. **Mengelola Session Pengguna** - Sistem mengelola session dan validasi token pengguna secara otomatis
3. **Upload Dokumen PDF** - Pengguna mengunggah file PDF yang akan diproses menjadi peta konsep
4. **Validasi File PDF** - Sistem memvalidasi format, ukuran, dan integritas file yang diunggah
5. **Ekstraksi Teks dari PDF** - Sistem mengekstrak teks dari dokumen PDF menggunakan AI
6. **Generate Peta Konsep dengan AI** - AI menganalisis teks dan menghasilkan konsep serta relasi antar konsep
7. **Visualisasi Peta Konsep Interaktif** - Sistem menampilkan peta konsep dalam format visual yang interaktif
8. **Interaksi dengan Peta Konsep** - Pengguna dapat melakukan zoom, pan, dan navigasi pada peta konsep
9. **Pilih dan Lihat Detail Node** - Pengguna dapat memilih node tertentu untuk melihat informasi detail
10. **Tanya Jawab AI per Node (RAG)** - Pengguna dapat bertanya tentang konsep tertentu dan mendapat jawaban kontekstual
11. **Simpan Riwayat Peta Konsep** - Sistem menyimpan setiap peta konsep yang dihasilkan ke dalam database
12. **Kelola Riwayat Peta Konsep** - Pengguna dapat melihat, mencari, dan menghapus riwayat peta konsep
13. **Load Peta Konsep dari Riwayat** - Pengguna dapat memuat kembali peta konsep yang pernah dibuat sebelumnya
14. **Logout** - Pengguna keluar dari sistem dan mengakhiri session aktif

---

## 6. Use Case Descriptions

### UC1: Login dengan Google OAuth
**Aktor:** Pengguna  
**Deskripsi:** Pengguna melakukan autentikasi ke sistem menggunakan akun Google mereka  
**Precondition:** Pengguna memiliki akun Google yang valid  
**Postcondition:** Pengguna berhasil terautentikasi dan mendapat akses ke sistem  
**Flow:**
1. Pengguna mengklik tombol "Login with Google"
2. Sistem mengarahkan ke halaman OAuth Google
3. Pengguna memasukkan kredensial Google
4. Google mengirim token ke sistem
5. Sistem memvalidasi token dan membuat session
6. Pengguna diarahkan ke dashboard

### UC2: Upload Dokumen PDF
**Aktor:** Pengguna  
**Deskripsi:** Pengguna mengunggah file PDF untuk diproses menjadi peta konsep  
**Precondition:** Pengguna sudah login ke sistem  
**Postcondition:** File PDF berhasil diunggah dan siap diproses  
**Flow:**
1. Pengguna memilih file PDF dari device
2. Sistem memvalidasi format dan ukuran file
3. File diunggah ke server
4. Sistem mengkonfirmasi upload berhasil

### UC3: Generate Peta Konsep dengan AI
**Aktor:** Sistem AI  
**Deskripsi:** AI menganalisis dokumen PDF dan menghasilkan peta konsep  
**Precondition:** File PDF telah berhasil diunggah  
**Postcondition:** Peta konsep dengan nodes dan edges berhasil dibuat  
**Flow:**
1. Sistem ekstrak teks dari PDF
2. AI menganalisis konten dan mengidentifikasi konsep utama
3. AI menentukan relasi antar konsep
4. Sistem membuat struktur peta konsep (nodes + edges)
5. Data peta konsep disimpan ke database

### UC4: Interaksi dengan Peta Konsep
**Aktor:** Pengguna  
**Deskripsi:** Pengguna berinteraksi dengan visualisasi peta konsep  
**Precondition:** Peta konsep telah berhasil dibuat dan ditampilkan  
**Postcondition:** Pengguna dapat menavigasi dan mengeksplorasi peta konsep  
**Flow:**
1. Pengguna melihat visualisasi peta konsep
2. Pengguna dapat zoom in/out
3. Pengguna dapat melakukan pan/drag
4. Pengguna dapat mengklik node untuk detail
5. Sistem merespons setiap interaksi dengan smooth

### UC5: Tanya Jawab AI per Node
**Aktor:** Pengguna, Sistem AI  
**Deskripsi:** Pengguna bertanya tentang konsep tertentu dan mendapat jawaban kontekstual  
**Precondition:** Pengguna telah memilih node tertentu pada peta konsep  
**Postcondition:** Pengguna mendapat jawaban yang relevan tentang konsep tersebut  
**Flow:**
1. Pengguna mengklik node spesifik
2. Panel detail node terbuka
3. Pengguna mengetik pertanyaan tentang konsep
4. Sistem memproses pertanyaan dengan RAG
5. AI memberikan jawaban berdasarkan konten dokumen
6. Jawaban ditampilkan di chat interface

### UC6: Kelola Riwayat Peta Konsep
**Aktor:** Pengguna  
**Deskripsi:** Pengguna mengelola riwayat peta konsep yang pernah dibuat  
**Precondition:** Pengguna sudah login dan memiliki riwayat peta konsep  
**Postcondition:** Pengguna dapat mengakses, mencari, atau menghapus riwayat  
**Flow:**
1. Pengguna membuka sidebar riwayat
2. Sistem menampilkan daftar peta konsep sebelumnya
3. Pengguna dapat mencari berdasarkan nama/tanggal
4. Pengguna dapat memilih peta konsep untuk dibuka kembali
5. Pengguna dapat menghapus riwayat yang tidak diperlukan

---

## 7. General Architecture & Deployment

### 7.1 General Architecture

**Deskripsi:** Arsitektur umum sistem CMVS menggunakan pola client-server dengan pemisahan yang jelas antara frontend dan backend. Sistem dibangun dengan prinsip microservices dan RESTful API untuk memastikan scalability dan maintainability.

#### 7.1.1 Architecture Diagram (Mermaid)
```mermaid
graph TB
    subgraph "Client Layer (Netlify)"
        FE[Frontend - Next.js<br/>🔧 Built with GitHub Actions]
        FE --> |HTTPS/REST API| API
    end
    
    subgraph "Server Layer (Render) - Python"
        API[Monolithic FastAPI Server<br/>🔧 Built with GitHub Actions]
        AUTH[Authentication Service]
        DOC[Document Processing Service]
        AI[AI Processing Service]
        CHAT[Chat/RAG Service]
        
        API -.-> AUTH
        API -.-> DOC
        API -.-> AI
        API -.-> CHAT
    end
    
    subgraph "Data Layer"
        DB[(MongoDB Atlas)]
        S3[Cloudflare R2 Storage]
        
        AUTH --> DB
        DOC --> S3
        AI --> DB
        CHAT --> DB
    end
    
    subgraph "External Services"
        GOOGLE[Google OAuth]
        GroqCloud["Llama3 (GroqCloud API)"]

        AUTH --> GOOGLE
        AI --> GroqCloud
        CHAT --> GroqCloud
    end
    
    subgraph "CI/CD"
        GHA[GitHub Actions<br/>🔄 Build & Deploy Pipeline]
        GHA -.-> FE
        GHA -.-> API
    end
```

**Catatan Arsitektur:**
- **Server Layer**: Menggunakan Python dengan FastAPI sebagai monolithic application
- **Deployment**: Frontend di Netlify, Backend di Render  
- **CI/CD**: GitHub Actions untuk build dan deploy otomatis (FE & BE)
- **Services**: Meskipun monolithic, kode diorganisir dalam service layers yang terpisah

#### 7.1.2 Architecture Diagram (PlantUML)

```plantuml
@startuml
!theme plain

' Define the layout direction
top to bottom direction

' Client Layer
package "Client Layer - Next.js" <<Deployed on Netlify>> {
  [Frontend - Next.js] as FE
}

' Server Layer
package "Server Layer - Python" <<Deployed on Render>> {
  [Monolithic FastAPI Server] as API
  [Authentication Service] as AUTH
  [Document Processing Service] as DOC
  [AI Processing Service] as AI
  [Chat/RAG Service] as CHAT
}

' Data Layer
package "Data Layer" {
  database DB as "MongoDB Atlas"
  node S3 as "Cloudflare R2 Storage"
}

' External Services
package "External Services" {
  [Google OAuth] as GOOGLE
  [Llama3 (GroqCloud API)] as GroqCloud
}

' Connections
FE --> API : HTTPS/REST API

' Internal service organization (monolithic but organized)
API ..> AUTH : contains
API ..> DOC : contains
API ..> AI : contains
API ..> CHAT : contains

AUTH --> DB
DOC --> S3
AI --> DB
CHAT --> DB

AUTH --> GOOGLE
AI --> GroqCloud
CHAT --> GroqCloud

@enduml
```

**Catatan Arsitektur:**
- **Monolithic Design**: Single FastAPI application dengan service layers terorganisir
- **Python Backend**: Seluruh server layer menggunakan Python
- **Deployment Platforms**: Frontend → Netlify, Backend → Render
- **CI/CD**: GitHub Actions untuk automated build dan deployment
- **Service Organization**: Meskipun monolithic, kode tetap terstruktur dalam service layers

### 7.2 Frontend Architecture (Next.js)

**Framework:** Next.js 14 dengan App Router  
**Styling:** Tailwind CSS + Shadcn/ui  
**State Management:** Zustand  
**Authentication:** NextAuth.js  
**Key Features:**
- Server-side rendering (SSR) untuk SEO optimization
- Client-side routing untuk smooth navigation
- Responsive design dengan mobile-first approach
- Real-time updates menggunakan WebSocket/polling
- Progressive Web App (PWA) capabilities

**Component Structure:**
- **Layout Components:** AppLayoutWrapper, MobileHeader
- **Auth Components:** AuthDialog, GoogleAuthProvider
- **Core Components:** HierarchicalMindMapDisplay, NodeDetailPanel
- **Utility Components:** FileDropZone, HistorySidebar, ThemeProvider

### 7.3 Backend Architecture (FastAPI)

**Framework:** FastAPI dengan Python 3.11+  
**Database:** MongoDB Atlas  
**File Storage:** Cloudflare R2  
**Caching:** Redis  
**AI Integration:** Llama3 (GroqCloud API)  
**Key Features:**
- Asynchronous request handling untuk performance
- Automatic API documentation dengan Swagger/OpenAPI
- JWT-based authentication dengan refresh tokens
- File processing dengan background tasks
- Rate limiting dan error handling

**Service Structure:**
- **Auth Service:** User authentication dan session management
- **Document Service:** PDF upload, validation, dan text extraction
- **AI Service:** Concept map generation dengan Llama3 (GroqCloud API)
- **Chat Service:** RAG implementation untuk Q&A
- **User Service:** User profile dan preferences management

### 7.4 Deployment Architecture

#### CI/CD Pipeline (GitHub Actions)

**Build & Deployment Process:**

- **Frontend (Next.js)**: 
  - GitHub Actions workflow triggers pada push ke main branch
  - Build process: `npm run build` 
  - Deploy target: Netlify
  - Build artifacts: Static files di `out/` directory

- **Backend (FastAPI)**:
  - GitHub Actions workflow triggers pada push ke main branch  
  - Build process: `pip install -r requirements.txt`
  - Deploy target: Render
  - Build artifacts: Python application bundle

#### Frontend Deployment (Netlify)

**Platform:** Netlify  
**Build Process:** 
- Automatic builds dari GitHub repository
- Build command: `npm run build`
- Deploy dari `frontend/` directory

**Features:**
- CDN global untuk fast loading
- Automatic HTTPS dengan custom domain
- Branch previews untuk testing
- Form handling untuk contact/feedback
- Analytics dan performance monitoring

**Configuration (netlify.toml):**
```toml
[build]
  base = "frontend/"
  command = "npm run build"
  publish = "out/"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/api/*"
  to = "https://cmvs-backend.render.com/api/:splat"
  status = 200
```

#### Backend Deployment (Render)

**Platform:** Render  
**Service Type:** Web Service  
**Build Process:**
- Automatic builds dari GitHub repository
- Build command: `pip install -r requirements.txt`
- Start command: `python uvicorn_runner.py`

**Features:**
- Automatic HTTPS dan custom domain
- Auto-scaling berdasarkan traffic
- Health checks dan monitoring
- Database connection pooling

#### Database & Storage

**MongoDB Atlas:**
- Cloud-hosted MongoDB dengan auto-scaling
- Global clusters untuk low latency
- Automatic backups dan point-in-time recovery
- Built-in security dengan IP whitelisting

**Cloudflare R2:**
- File storage untuk uploaded PDFs
- Lifecycle policies untuk cost optimization
- CloudFront CDN untuk fast file delivery
- Versioning dan backup capabilities

#### Monitoring & Analytics

**Monitoring Tools:**
- Render native monitoring untuk backend
- Netlify Analytics untuk frontend
- MongoDB Atlas monitoring untuk database
- Custom logging dengan structured logs

**Performance Metrics:**
- API response times
- File processing duration
- User engagement metrics
- Error rates dan uptime monitoring

---

**Catatan:** Diagram ini memberikan gambaran umum arsitektur sistem CMVS. Implementasi detail dapat disesuaikan berdasarkan kebutuhan spesifik dan feedback dari testing.