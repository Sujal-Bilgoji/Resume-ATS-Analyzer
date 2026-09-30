import { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobDescription, setJobDescription] = useState("");

  // Runs when the user selects a file
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setMessage("");
    setResumeText("");

    if (!selectedFile) {
      setFile(null);
      return;
    }

    // Check if the selected file is a PDF
    if (selectedFile.type !== "application/pdf") {
      setFile(null);
      setMessage("Please select a PDF file.");
      return;
    }

    setFile(selectedFile);
  };

  // Sends the PDF to FastAPI
  const uploadResume = async () => {
    if (!file) {
      setMessage("Please select a PDF resume first.");
      return;
    }

    // FormData is used to send files
    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");
      setResumeText("");

      const response = await fetch(
        "http://127.0.0.1:8000/api/upload-resume",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setMessage(
        `Uploaded: ${data.filename} (${data.pages} page${
          data.pages === 1 ? "" : "s"
        })`
      );

      setResumeText(data.text);
    } catch (error) {
      console.error(error);
      setMessage("Could not upload the resume.");
    } finally {
      setLoading(false);
    }
  };

  // Sends the Job Description to FastAPI
  const submitJobDescription = async () => {
    if (!jobDescription.trim()) {
      setMessage("Please enter a job description first.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/job-description",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            job_description: jobDescription,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Job description submission failed");
      }

      const data = await response.json();

      setMessage(data.message);

      console.log(
  "Job Description received by FastAPI:",
  data.job_description
);

console.log(
  "Extracted JD Skills:",
  data.skills
);
    } catch (error) {
      console.error(error);
      setMessage("Could not send the job description.");
    }
  };

  return (
    <div>
      <h1>ATS Resume Analyzer</h1>

      <p>Upload your resume in PDF format.</p>

      <input
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
      />

      {file && <p>Selected file: {file.name}</p>}

      <button onClick={uploadResume} disabled={loading}>
        {loading ? "Uploading..." : "Upload Resume"}
      </button>

      <h2>Job Description</h2>

      <textarea
        value={jobDescription}
        onChange={(event) => setJobDescription(event.target.value)}
        placeholder="Paste the job description here..."
        rows="12"
        cols="80"
      />

      <br />

      <button onClick={submitJobDescription}>
        Submit Job Description
      </button>

      {message && <p>{message}</p>}

      {resumeText && (
        <div>
          <h2>Extracted Resume Text</h2>

          <pre style={{ whiteSpace: "pre-wrap" }}>
            {resumeText}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;