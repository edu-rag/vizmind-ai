# KEBUTUHAN FUNGSIONAL SISTEM
## AI-Powered Concept Map Visual Synthesizer (CMVS)

---

**Nama Sistem:** AI-Powered Concept Map Visual Synthesizer (CMVS)  
**Versi Dokumen:** 1.0  
**Tanggal:** 1 Juli 2025  
**Bahasa:** Bahasa Indonesia  

---

## 1. PENDAHULUAN

### 1.1 Tujuan Dokumen
Dokumen ini mendeskripsikan kebutuhan fungsional sistem AI-Powered Concept Map Visual Synthesizer (CMVS), yang merupakan aplikasi web berbasis AI untuk mengkonversi dokumen PDF menjadi peta konsep interaktif dan menyediakan fitur tanya jawab berbasis Retrieval Augmented Generation (RAG).

### 1.2 Ruang Lingkup Sistem
Sistem CMVS adalah aplikasi web full-stack yang terdiri dari:
- Frontend berbasis Next.js dengan TypeScript
- Backend API berbasis FastAPI dengan Python
- Integrasi AI/LLM untuk pemrosesan dokumen dan generasi peta konsep
- Sistem autentikasi Google OAuth
- Penyimpanan data MongoDB Atlas dengan vector search
- Penyimpanan file S3-compatible

### 1.3 Definisi dan Istilah
- **CMVS**: Concept Map Visual Synthesizer
- **RAG**: Retrieval Augmented Generation
- **JWT**: JSON Web Token
- **Peta Konsep**: Representasi visual dari hubungan antar konsep dalam suatu topik
- **Node**: Elemen individual dalam peta konsep yang merepresentasikan sebuah konsep
- **Edge**: Garis penghubung yang menunjukkan relasi antar konsep

---

## 2. RINGKASAN KEBUTUHAN FUNGSIONAL

### 2.1 Tabel Ringkasan Semua Functional Requirements

| Kategori                                         | Total FR | Deskripsi                                                                           |
| ------------------------------------------------ | -------- | ----------------------------------------------------------------------------------- |
| Autentikasi dan Manajemen Pengguna               | 3        | Google OAuth login, session management, route protection                            |
| Upload dan Pemrosesan Dokumen                    | 3        | Upload PDF, validasi file, penyimpanan S3                                           |
| Generasi Peta Konsep                             | 4        | Ekstraksi teks, chunking, ekstraksi konsep, visualisasi                             |
| Tampilan dan Interaksi Peta Konsep               | 4        | Render interaktif, fullscreen, node selection, theme toggle                         |
| Manajemen History dan Session                    | 4        | Simpan history, tampilkan sidebar, load dari history, delete                        |
| Fitur Chat dan Q&A (RAG) dalam Node Detail Panel | 4        | Q&A interface dalam node panel, contextual Q&A, session history, source attribution |
| Responsive Design dan Mobile Support             | 3        | Mobile-first design, mobile navigation, touch interactions                          |
| Performance dan Error Handling                   | 3        | Loading states, error handling, optimistic updates                                  |
| **Total**                                        | **28**   | **Keseluruhan Functional Requirements**                                             |

---

### 2.2 Tabel Functional Requirements General

| ID             | Nama Fitur         | Kategori        | Deskripsi                                                                                                        | Prioritas | Status |
| -------------- | ------------------ | --------------- | ---------------------------------------------------------------------------------------------------------------- | --------- | ------ |
| FR-AUTH-001    | Login Google OAuth | Authentication  | Sistem menyediakan fitur login menggunakan akun Google dengan integrasi OAuth dan generasi JWT token             | High      | ✅      |
| FR-AUTH-002    | Manajemen Session  | Authentication  | Sistem mengelola session pengguna dengan JWT, validasi token, dan fungsi logout                                  | High      | ✅      |
| FR-AUTH-003    | Proteksi Route     | Authentication  | Sistem melindungi route tertentu yang memerlukan autentikasi (upload, history, Q&A)                              | High      | ✅      |
| FR-UPLOAD-001  | Upload File PDF    | File Management | Sistem menyediakan antarmuka drag-and-drop untuk upload multiple file PDF dengan validasi dan progress indicator | High      | ✅      |
| FR-UPLOAD-002  | Validasi File      | File Management | Sistem memvalidasi format, ukuran, dan integritas file PDF yang diupload                                         | High      | ✅      |
| FR-UPLOAD-003  | Penyimpanan File   | File Management | Sistem menyimpan file PDF ke storage S3-compatible dengan nama unik dan metadata                                 | High      | ✅      |
| FR-CMVS-001    | Ekstraksi Teks PDF | AI Processing   | Sistem mengekstrak teks dari file PDF dengan mempertahankan struktur dan konteks                                 | High      | ✅      |
| FR-CMVS-002    | Chunking Teks      | AI Processing   | Sistem membagi teks panjang menjadi chunk-chunk optimal untuk pemrosesan LLM                                     | High      | ✅      |
| FR-CMVS-003    | Ekstraksi Konsep   | AI Processing   | Sistem mengekstrak konsep-konsep utama dan relasi antar konsep menggunakan LLM                                   | High      | ✅      |
| FR-CMVS-004    | Visualisasi Peta   | AI Processing   | Sistem mengubah concept triples menjadi format visualisasi ReactFlow yang interaktif                             | High      | ✅      |
| FR-DISPLAY-001 | Render Interaktif  | Visualization   | Sistem menampilkan peta konsep interaktif dengan fitur click, zoom, drag, dan responsive design                  | High      | ✅      |
| FR-DISPLAY-002 | Mode Fullscreen    | Visualization   | Sistem menyediakan mode fullscreen untuk peta konsep dengan toggle button                                        | Medium    | ✅      |
| FR-DISPLAY-003 | Node Selection     | Visualization   | Sistem menampilkan detail dan highlight ketika node dipilih dengan panel detail                                  | High      | ✅      |
| FR-DISPLAY-004 | Theme Toggle       | UI/UX           | Sistem menyediakan toggle antara light dan dark mode dengan penyimpanan preferensi                               | Low       | ✅      |
| FR-HISTORY-001 | Simpan History     | Data Management | Sistem menyimpan riwayat peta konsep dengan metadata lengkap dan timestamp                                       | High      | ✅      |
| FR-HISTORY-002 | Sidebar History    | Data Management | Sistem menampilkan sidebar dengan daftar peta konsep, search, dan filter capability                              | High      | ✅      |
| FR-HISTORY-003 | Load dari History  | Data Management | Sistem dapat memuat kembali peta konsep dari history dengan transisi smooth                                      | High      | ✅      |
| FR-HISTORY-004 | Delete History     | Data Management | Sistem menyediakan fungsi hapus peta konsep dengan konfirmasi dialog                                             | Medium    | ✅      |
| FR-CHAT-001    | Q&A Interface      | AI Interaction  | Sistem menyediakan interface Q&A dalam Node Detail Panel untuk berinteraksi dengan konsep spesifik               | High      | ✅      |
| FR-CHAT-002    | Contextual Q&A     | AI Interaction  | Sistem menjawab pertanyaan berdasarkan konteks dokumen dan konsep yang dipilih menggunakan RAG pipeline          | High      | ✅      |
| FR-CHAT-003    | Session History    | AI Interaction  | Sistem menyimpan dan menampilkan riwayat percakapan per node selama session browser                              | Medium    | ✅      |
| FR-CHAT-004    | Source Attribution | AI Interaction  | Sistem menampilkan sumber informasi dan confidence score untuk setiap jawaban dalam context node                 | Medium    | ✅      |
| FR-MOBILE-001  | Mobile Design      | Responsive      | Sistem dioptimasi untuk penggunaan mobile dengan layout responsif dan touch-friendly controls                    | High      | ✅      |
| FR-MOBILE-002  | Mobile Navigation  | Responsive      | Sistem menyediakan navigasi mobile dengan hamburger menu dan collapsible sidebars                                | High      | ✅      |
| FR-MOBILE-003  | Touch Interactions | Responsive      | Sistem mendukung touch interactions seperti pinch to zoom, drag, dan long press                                  | Medium    | ✅      |
| FR-PERF-001    | Loading States     | Performance     | Sistem menampilkan loading states dengan progress bar, skeleton, dan spinner                                     | Medium    | ✅      |
| FR-PERF-002    | Error Handling     | Performance     | Sistem menangani error dengan graceful handling, toast notifications, dan retry mechanisms                       | High      | ✅      |
| FR-PERF-003    | Optimistic Updates | Performance     | Sistem menggunakan optimistic updates untuk responsivitas dengan rollback mechanism                              | Medium    | ✅      |

---

### 2.3 Analisis Komponen Frontend

| Komponen Frontend          | Jumlah FR | Functional Requirements                                              | Deskripsi Fungsi                                         |
| -------------------------- | --------- | -------------------------------------------------------------------- | -------------------------------------------------------- |
| **ConceptMapDisplay.tsx**  | 4         | FR-CMVS-004, FR-DISPLAY-001, FR-DISPLAY-002, FR-MOBILE-003           | Komponen utama untuk rendering dan interaksi peta konsep |
| **NodeDetailPanel.tsx**    | 5         | FR-DISPLAY-003, FR-CHAT-001, FR-CHAT-002, FR-CHAT-003, FR-CHAT-004   | Panel detail node dengan fitur Q&A terintegrasi          |
| **FileDropZone.tsx**       | 2         | FR-UPLOAD-001, FR-UPLOAD-002                                         | Zona upload file dengan validasi                         |
| **HistorySidebar.tsx**     | 3         | FR-HISTORY-002, FR-HISTORY-003, FR-HISTORY-004                       | Sidebar manajemen history peta konsep                    |
| **GoogleAuthProvider.tsx** | 1         | FR-AUTH-001                                                          | Provider autentikasi Google OAuth                        |
| **AuthDialog.tsx**         | 1         | FR-AUTH-002                                                          | Dialog manajemen session                                 |
| **AppLayoutWrapper.tsx**   | 1         | FR-AUTH-003                                                          | Wrapper layout dengan proteksi route                     |
| **ThemeToggle.tsx**        | 1         | FR-DISPLAY-004                                                       | Toggle tema light/dark                                   |
| **MobileHeader.tsx**       | 1         | FR-MOBILE-002                                                        | Header navigasi mobile                                   |
| **Skeleton Components**    | 1         | FR-PERF-001                                                          | Komponen loading state                                   |
| **Toast Notifications**    | 1         | FR-PERF-002                                                          | Sistem notifikasi error                                  |
| **Zustand Store**          | 1         | FR-PERF-003                                                          | State management global                                  |
| **All Components**         | 1         | FR-MOBILE-001                                                        | Responsive design universal                              |
| **Backend Integration**    | 4         | FR-UPLOAD-003, FR-CMVS-001, FR-CMVS-002, FR-CMVS-003, FR-HISTORY-001 | Integrasi dengan backend services                        |

### 2.4 Statistik Implementation Frontend

| Metrik                            | Nilai | Keterangan                                 |
| --------------------------------- | ----- | ------------------------------------------ |
| **Total Functional Requirements** | 28    | Keseluruhan FR yang diimplementasikan      |
| **Frontend Components Utama**     | 13    | Komponen React yang mengimplementasikan FR |
| **Backend Integration Points**    | 5     | FR yang memerlukan integrasi backend       |
| **High Priority Features**        | 18    | FR dengan prioritas tinggi                 |
| **Medium Priority Features**      | 8     | FR dengan prioritas menengah               |
| **Low Priority Features**         | 2     | FR dengan prioritas rendah                 |
| **Completion Rate**               | 100%  | Semua FR telah diimplementasikan           |

### 2.5 User Journey Mapping dengan Functional Requirements

| Tahap User Journey            | Functional Requirements                                        | Komponen Terlibat                                | Pengalaman Pengguna                                                    |
| ----------------------------- | -------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------- |
| **1. Masuk ke Sistem**        | FR-AUTH-001, FR-AUTH-002, FR-AUTH-003                          | GoogleAuthProvider, AuthDialog, AppLayoutWrapper | Pengguna login dengan Google, session dikelola, akses route dilindungi |
| **2. Upload Dokumen**         | FR-UPLOAD-001, FR-UPLOAD-002, FR-UPLOAD-003                    | FileDropZone                                     | Pengguna upload PDF dengan drag-drop, file divalidasi dan disimpan     |
| **3. Proses AI Generasi**     | FR-CMVS-001, FR-CMVS-002, FR-CMVS-003, FR-CMVS-004             | Backend + ConceptMapDisplay                      | Sistem ekstrak teks, buat chunk, ekstrak konsep, generate visualisasi  |
| **4. Eksplorasi Peta Konsep** | FR-DISPLAY-001, FR-DISPLAY-002, FR-DISPLAY-003                 | ConceptMapDisplay, NodeDetailPanel               | Pengguna interaksi dengan peta, fullscreen, pilih node untuk detail    |
| **5. Q&A dengan AI**          | FR-CHAT-001, FR-CHAT-002, FR-CHAT-003, FR-CHAT-004             | NodeDetailPanel                                  | Pengguna bertanya tentang konsep, mendapat jawaban kontekstual         |
| **6. Manajemen History**      | FR-HISTORY-001, FR-HISTORY-002, FR-HISTORY-003, FR-HISTORY-004 | HistorySidebar                                   | Pengguna lihat, load, dan hapus history peta konsep                    |
| **7. Penggunaan Mobile**      | FR-MOBILE-001, FR-MOBILE-002, FR-MOBILE-003                    | All Components, MobileHeader                     | Pengguna akses sistem melalui mobile dengan experience optimal         |
| **8. Pengalaman Umum**        | FR-DISPLAY-004, FR-PERF-001, FR-PERF-002, FR-PERF-003          | ThemeToggle, Skeleton, Toast, Store              | Theme customization, loading states, error handling, responsivitas     |

---

## 3. KEBUTUHAN FUNGSIONAL DETAIL

### 3.1 Autentikasi dan Manajemen Pengguna

| ID          | Nama Fitur                | Deskripsi                                                                                                  | Aktor    | Input                      | Output                          | Prasyarat                           |
| ----------- | ------------------------- | ---------------------------------------------------------------------------------------------------------- | -------- | -------------------------- | ------------------------------- | ----------------------------------- |
| FR-AUTH-001 | Login dengan Google OAuth | Sistem harus menyediakan fitur login menggunakan akun Google dengan integrasi OAuth dan generasi JWT token | Pengguna | Kredensial Google          | JWT token, data profil pengguna | Pengguna memiliki akun Google aktif |
| FR-AUTH-002 | Manajemen Session         | Sistem harus mengelola session pengguna dengan JWT, validasi token, dan fungsi logout                      | Sistem   | JWT token                  | Status validasi token           | -                                   |
| FR-AUTH-003 | Proteksi Route            | Sistem harus melindungi route tertentu yang memerlukan autentikasi (upload, history, chat)                 | Sistem   | Request dengan/tanpa token | Akses granted/denied            | -                                   |

### 3.2 Upload dan Pemrosesan Dokumen

| ID            | Nama Fitur       | Deskripsi                                                                                                              | Aktor                    | Input               | Output                         | Prasyarat            |
| ------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------ | ------------------- | ------------------------------ | -------------------- |
| FR-UPLOAD-001 | Upload File PDF  | Sistem harus menyediakan antarmuka drag-and-drop untuk upload multiple file PDF dengan validasi dan progress indicator | Pengguna terauthentikasi | File PDF            | Status upload, preview file    | Pengguna sudah login |
| FR-UPLOAD-002 | Validasi File    | Sistem harus memvalidasi format, ukuran, dan integritas file PDF yang diupload                                         | Sistem                   | File yang diupload  | Status validasi, pesan error   | -                    |
| FR-UPLOAD-003 | Penyimpanan File | Sistem harus menyimpan file PDF ke storage S3-compatible dengan nama unik dan metadata                                 | Sistem                   | File PDF yang valid | URL file, metadata penyimpanan | -                    |

### 3.3 Generasi Peta Konsep

| ID          | Nama Fitur                       | Deskripsi                                                                              | Aktor               | Input           | Output                                          | Prasyarat |
| ----------- | -------------------------------- | -------------------------------------------------------------------------------------- | ------------------- | --------------- | ----------------------------------------------- | --------- |
| FR-CMVS-001 | Ekstraksi Teks dari PDF          | Sistem harus mengekstrak teks dari file PDF dengan mempertahankan struktur dan konteks | Sistem              | File PDF        | Teks yang diekstrak                             | -         |
| FR-CMVS-002 | Chunking Teks                    | Sistem harus membagi teks panjang menjadi chunk-chunk optimal untuk pemrosesan LLM     | Sistem              | Teks ekstraksi  | Array chunk teks                                | -         |
| FR-CMVS-003 | Ekstraksi Konsep dan Relasi      | Sistem harus mengekstrak konsep-konsep utama dan relasi menggunakan LLM                | Sistem (dengan LLM) | Chunk teks      | List concept triples (source, relation, target) | -         |
| FR-CMVS-004 | Generasi Visualisasi Peta Konsep | Sistem harus mengubah concept triples menjadi format visualisasi ReactFlow             | Sistem              | Concept triples | ReactFlow data structure (nodes, edges)         | -         |

### 3.4 Tampilan dan Interaksi Peta Konsep

| ID             | Nama Fitur                    | Deskripsi                                                                                             | Aktor    | Input                                | Output                   | Prasyarat |
| -------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------- | -------- | ------------------------------------ | ------------------------ | --------- |
| FR-DISPLAY-001 | Render Peta Konsep Interaktif | Sistem harus menampilkan peta konsep interaktif dengan fitur click, zoom, drag, dan responsive design | Pengguna | User interaction (click, drag, zoom) | Updated visualization    | -         |
| FR-DISPLAY-002 | Mode Fullscreen               | Sistem harus menyediakan mode fullscreen untuk peta konsep dengan toggle button                       | Pengguna | Click fullscreen toggle              | Fullscreen/windowed view | -         |
| FR-DISPLAY-003 | Node Selection dan Detail     | Sistem harus menampilkan detail dan highlight ketika node dipilih                                     | Pengguna | Click pada node                      | Node detail panel        | -         |
| FR-DISPLAY-004 | Theme Toggle                  | Sistem harus menyediakan toggle antara light dan dark mode dengan penyimpanan preferensi              | Pengguna | Click theme toggle                   | Theme mode change        | -         |

### 3.5 Manajemen History dan Session

| ID             | Nama Fitur                    | Deskripsi                                                                                 | Aktor    | Input                      | Output                  | Prasyarat |
| -------------- | ----------------------------- | ----------------------------------------------------------------------------------------- | -------- | -------------------------- | ----------------------- | --------- |
| FR-HISTORY-001 | Simpan History Peta Konsep    | Sistem harus menyimpan riwayat peta konsep dengan metadata lengkap dan timestamp          | Sistem   | Generated concept map      | Saved map record        | -         |
| FR-HISTORY-002 | Tampilkan Sidebar History     | Sistem harus menampilkan sidebar dengan daftar peta konsep, search, dan filter capability | Pengguna | -                          | List of historical maps | -         |
| FR-HISTORY-003 | Load Peta Konsep dari History | Sistem harus dapat memuat kembali peta konsep dari history dengan transisi smooth         | Pengguna | Click history item         | Loaded concept map      | -         |
| FR-HISTORY-004 | Delete Peta Konsep            | Sistem harus menyediakan fungsi hapus peta konsep dengan konfirmasi dialog                | Pengguna | Delete action confirmation | Updated history list    | -         |

### 3.6 Fitur Chat dan Q&A (RAG)

| ID          | Nama Fitur                     | Deskripsi                                                                                                   | Aktor                 | Input                       | Output                           | Prasyarat    |
| ----------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------- | --------------------- | --------------------------- | -------------------------------- | ------------ |
| FR-CHAT-001 | Q&A Interface dalam Node Panel | Sistem harus menyediakan Q&A interface dalam Node Detail Panel dengan input field dan history               | Pengguna              | Node selection, text input  | Q&A interface in node panel      | Node dipilih |
| FR-CHAT-002 | Contextual Question Answering  | Sistem harus menjawab pertanyaan berdasarkan konteks dokumen dan node yang dipilih menggunakan RAG pipeline | Sistem (RAG pipeline) | User question, node context | AI-generated answer with sources | -            |
| FR-CHAT-003 | Session History per Node       | Sistem harus menyimpan dan menampilkan riwayat percakapan per node selama session browser                   | Sistem                | Chat messages per node      | Stored session history per node  | -            |
| FR-CHAT-004 | Source Attribution             | Sistem harus menampilkan sumber informasi dan confidence score untuk setiap jawaban dalam context node      | Sistem                | Generated answer            | Source citations and references  | -            |

### 3.7 Responsive Design dan Mobile Support

| ID            | Nama Fitur          | Deskripsi                                                                                           | Aktor           | Input              | Output               | Prasyarat |
| ------------- | ------------------- | --------------------------------------------------------------------------------------------------- | --------------- | ------------------ | -------------------- | --------- |
| FR-MOBILE-001 | Mobile-First Design | Sistem harus dioptimasi untuk penggunaan mobile dengan layout responsif dan touch-friendly controls | Pengguna mobile | Touch interactions | Responsive interface | -         |
| FR-MOBILE-002 | Mobile Navigation   | Sistem harus menyediakan navigasi mobile dengan hamburger menu dan collapsible sidebars             | Pengguna mobile | Touch gestures     | Mobile navigation    | -         |
| FR-MOBILE-003 | Touch Interactions  | Sistem harus mendukung touch interactions seperti pinch to zoom, drag, dan long press               | Pengguna mobile | Touch gestures     | Map interactions     | -         |

### 3.8 Performance dan Error Handling

| ID          | Nama Fitur         | Deskripsi                                                                                        | Aktor  | Input                   | Output                              | Prasyarat |
| ----------- | ------------------ | ------------------------------------------------------------------------------------------------ | ------ | ----------------------- | ----------------------------------- | --------- |
| FR-PERF-001 | Loading States     | Sistem harus menampilkan loading states dengan progress bar, skeleton, dan spinner               | Sistem | Long-running operations | Loading indicators                  | -         |
| FR-PERF-002 | Error Handling     | Sistem harus menangani error dengan graceful handling, toast notifications, dan retry mechanisms | Sistem | Error conditions        | Error messages and recovery options | -         |
| FR-PERF-003 | Optimistic Updates | Sistem harus menggunakan optimistic updates untuk responsivitas dengan rollback mechanism        | Sistem | User actions            | Immediate UI feedback               | -         |

### 3.9 Traceability Matrix

| Functional Requirement | Frontend Component     | Backend Service    | Database Collection | External API     |
| ---------------------- | ---------------------- | ------------------ | ------------------- | ---------------- |
| FR-AUTH-001            | GoogleAuthProvider.tsx | user_service.py    | users               | Google OAuth API |
| FR-AUTH-002            | AuthDialog.tsx         | security.py        | -                   | -                |
| FR-AUTH-003            | AppLayoutWrapper.tsx   | middleware         | -                   | -                |
| FR-UPLOAD-001          | FileDropZone.tsx       | pdf_service.py     | cmvs_documents      | -                |
| FR-UPLOAD-002          | FileDropZone.tsx       | pdf_service.py     | -                   | -                |
| FR-UPLOAD-003          | -                      | s3_service.py      | cmvs_documents      | S3 API           |
| FR-CMVS-001            | -                      | pdf_service.py     | -                   | -                |
| FR-CMVS-002            | -                      | cmvs_service.py    | chunks              | -                |
| FR-CMVS-003            | -                      | langgraph_pipeline | -                   | Groq/OpenAI API  |
| FR-CMVS-004            | ConceptMapDisplay.tsx  | cmvs_service.py    | cmvs_documents      | -                |
| FR-DISPLAY-001         | ConceptMapDisplay.tsx  | -                  | -                   | -                |
| FR-DISPLAY-002         | ConceptMapDisplay.tsx  | -                  | -                   | -                |
| FR-DISPLAY-003         | NodeDetailPanel.tsx    | -                  | -                   | -                |
| FR-DISPLAY-004         | ThemeToggle.tsx        | -                  | -                   | -                |
| FR-HISTORY-001         | -                      | cmvs_service.py    | cmvs_documents      | -                |
| FR-HISTORY-002         | HistorySidebar.tsx     | cmvs_service.py    | cmvs_documents      | -                |
| FR-HISTORY-003         | HistorySidebar.tsx     | cmvs_service.py    | cmvs_documents      | -                |
| FR-HISTORY-004         | HistorySidebar.tsx     | cmvs_service.py    | cmvs_documents      | -                |
| FR-CHAT-001            | NodeDetailPanel.tsx    | -                  | -                   | -                |
| FR-CHAT-002            | NodeDetailPanel.tsx    | langgraph_pipeline | chunks, embeddings  | Groq/OpenAI API  |
| FR-CHAT-003            | NodeDetailPanel.tsx    | -                  | session_storage     | -                |
| FR-MOBILE-001          | All components         | -                  | -                   | -                |
| FR-MOBILE-002          | MobileHeader.tsx       | -                  | -                   | -                |
| FR-MOBILE-003          | ConceptMapDisplay.tsx  | -                  | -                   | -                |
| FR-PERF-001            | Skeleton components    | -                  | -                   | -                |
| FR-PERF-002            | Toast notifications    | -                  | -                   | -                |
| FR-PERF-003            | Zustand store          | -                  | -                   | -                |

---

## 4. KEBUTUHAN NON-FUNGSIONAL

### 4.1 Performance

- Response time < 2 detik untuk operasi normal
- Upload file support hingga 50MB per file
- Concurrent users support minimal 100 users
- Map rendering time < 5 detik untuk dokumen standar

### 4.2 Usability

- Interface intuitif dengan learning curve minimal
- Accessibility compliance (WCAG 2.1)
- Multi-language support (saat ini Bahasa Inggris)
- Keyboard navigation support

### 4.3 Security

- HTTPS enforcement untuk semua komunikasi
- JWT token expiration dan refresh mechanism
- Input validation dan sanitization
- File upload security scanning

### 4.4 Compatibility

- Support browser modern (Chrome, Firefox, Safari, Edge)
- Mobile browser compatibility (iOS Safari, Chrome Mobile)
- Progressive Web App features
- Cross-platform compatibility

---

## 5. BATASAN SISTEM

### 5.1 Batasan Teknis

- Hanya mendukung file PDF sebagai input
- Maksimal ukuran file 50MB per upload
- Maksimal 10 file per batch upload
- Bahasa dokumen yang didukung: Bahasa Inggris dan Indonesia

### 5.2 Batasan Fungsional

- AI processing bergantung pada kualitas teks dalam PDF
- Akurasi concept extraction tergantung pada kompleksitas dokumen
- Tidak mendukung PDF dengan proteksi password
- Tidak mendukung PDF yang sebagian besar berisi gambar tanpa OCR

---

## 6. ASUMSI DAN DEPENDENSI

### 6.1 Asumsi

- Pengguna memiliki koneksi internet yang stabil
- Pengguna memiliki akun Google untuk autentikasi
- Browser pengguna mendukung JavaScript modern
- Dokumen PDF berisi teks yang dapat diekstrak

### 6.2 Dependensi Eksternal

- Google OAuth API untuk autentikasi
- OpenAI/Groq API untuk LLM processing
- MongoDB Atlas untuk database dan vector search
- AWS S3 atau S3-compatible storage untuk file storage

---

## 7. ACCEPTANCE CRITERIA

Setiap kebutuhan fungsional dianggap berhasil jika:

1. Implementasi sesuai dengan spesifikasi yang dideskripsikan
2. Testing manual dan otomatis berhasil tanpa error
3. Performance memenuhi standar yang ditetapkan
4. User experience sesuai dengan design requirement
5. Security measures berfungsi dengan baik

---

**Catatan:** Dokumen ini akan di-update seiring dengan perkembangan sistem dan feedback dari testing.
