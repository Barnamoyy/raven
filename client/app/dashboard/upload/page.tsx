/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
/**
 * v0 by Vercel.
 * @see https://v0.dev/t/aDFucFbMyb8
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import { useState } from "react";

import { useUser } from "@clerk/nextjs";

// state management
import { useDataStore } from "../../../store/useDataStore";

export default function Component() {
  // Properly type the file state
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const { setLatest } = useDataStore();

  const { user } = useUser();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }

    if (!user) {
      alert("User not authenticated.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // The backend is expecting user_id, but it's not being properly included in the request
    formData.append("user_id", user.id);

    console.log("User ID being sent:", user.id);
    console.log("File being sent:", file.name);

    setUploading(true);

    try {
      const response = await fetch("http://localhost:8000/storage/upload/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Server error:", errorData);
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      console.log("Upload successful:", result);

      setLatest(result);

      alert("File uploaded successfully!");
    } catch (error: unknown) {
      console.error("Upload error:", error);
      // Properly handle the error with type checking
      if (error instanceof Error) {
        alert(`File upload failed: ${error.message}`);
      } else {
        alert("File upload failed with an unknown error");
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 w-full h-full justify-center items-center">
      <Card className="w-fit h-fit">
        <CardContent className="p-6 space-y-4">
          <div className="border-2 border-dashed border-gray-200 rounded-lg flex flex-col gap-1 p-6 items-center">
            <FileIcon className="w-12 h-12" />
            <span className="text-sm font-medium text-gray-500">
              Drag and drop a file or click to browse
            </span>
            <span className="text-xs text-gray-500">.pcapng files only</span>
          </div>
          <div className="space-y-2 text-sm">
            <Label htmlFor="file" className="text-sm font-medium">
              File
            </Label>
            <Input
              id="file"
              type="file"
              accept=".pcapng"
              onChange={handleFileChange}
            />
            {file && (
              <div className="text-xs text-green-600 mt-1">
                Selected: {file.name}
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <Button size="lg" onClick={handleUpload} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

function FileIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
    </svg>
  );
}
