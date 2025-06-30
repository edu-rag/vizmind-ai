# Diagram Sistem Umum: AI-Powered Concept Map Visual Synthesizer (CMVS)

Dokumen ini berisi diagram-diagram tingkat tinggi (high-level) yang menggambarkan arsitektur dan alur kerja sistem CMVS dari perspektif umum, mencakup interaksi antara pengguna, frontend, dan backend.

---

## 1. Use Case Diagram (Mermaid)

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

## 2. Class Diagram (Mermaid)

**Deskripsi:** Class Diagram ini menyajikan komponen-komponen utama dalam sistem CMVS. Diagram ini menampilkan entitas kunci di frontend dan backend serta relasi dasarnya untuk memberikan gambaran struktur sistem secara umum.

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

---

## 3. Sequence Diagram (Mermaid)

**Deskripsi:** Sequence Diagram ini mengilustrasikan alur interaksi antar komponen sistem untuk skenario utama yaitu proses upload dokumen hingga peta konsep ditampilkan. Diagram ini menunjukkan urutan kejadian dan komunikasi antar komponen.

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
rectangle "Sistem CMVS" {
  
  ' Use Cases - Autentikasi
  usecase "Login dengan\nGoogle OAuth" as UC1
  usecase "Mengelola Session\nPengguna" as UC2
  
  ' Use Cases - Manajemen Dokumen
  usecase "Upload Dokumen PDF" as UC3
  usecase "Validasi File PDF" as UC4
  
  ' Use Cases - AI & Peta Konsep
  usecase "Ekstraksi Teks\ndari PDF" as UC5
  usecase "Generate Peta Konsep\ndengan AI" as UC6
  usecase "Visualisasi Peta Konsep\nInteraktif" as UC7
  
  ' Use Cases - Interaksi
  usecase "Interaksi dengan\nPeta Konsep" as UC8
  usecase "Pilih dan Lihat\nDetail Node" as UC9
  usecase "Tanya Jawab AI\nper Node (RAG)" as UC10
  
  ' Use Cases - Riwayat
  usecase "Simpan Riwayat\nPeta Konsep" as UC11
  usecase "Kelola Riwayat\nPeta Konsep" as UC12
  usecase "Load Peta Konsep\ndari Riwayat" as UC13
}

' Koneksi User dengan Use Cases
User --> UC1
User --> UC3
User --> UC8
User --> UC9
User --> UC10
User --> UC12
User --> UC13

' Include relationships (otomatis terjadi)
UC1 --> UC2 : <<include>>
UC3 --> UC4 : <<include>>
UC4 --> UC5 : <<include>>
UC5 --> UC6 : <<include>>
UC6 --> UC7 : <<include>>
UC7 --> UC11 : <<include>>

' Extend relationships (opsional)
UC8 ..> UC9 : <<extend>>
UC9 ..> UC10 : <<extend>>

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

---

**Catatan:** Diagram ini memberikan gambaran umum arsitektur sistem CMVS. Implementasi detail dapat disesuaikan berdasarkan kebutuhan spesifik dan feedback dari testing.