import { useState } from "react";
import { Box, Button, FileUpload, HStack, Text } from "@chakra-ui/react";
import { LuFileUp } from "react-icons/lu";
import { coreAPI } from "../../apiConfig";
import ErrorMsg from "../ui/ErrorMsg";

export interface ImportResult {
  file_ref: string;
  import_info: Record<string, unknown>;
}

interface DataImportProps {
  soniType: string;
  onImportSuccess: (result: ImportResult) => void;
  onImportError: (errorMessage: string) => void;
}

export function DataImport({
  soniType,
  onImportSuccess,
  onImportError,
}: DataImportProps) {
  const handleFileAccept = async (files: FileList | File[]) => {
    onImportError("");

    const file = files[0];
    if (!file) return;

    if (file.size > 1e7) {
      onImportError("File too large. Maximum size is 10MB.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("soni_type", soniType);

    try {
      const res = await fetch(`${coreAPI}/upload-data/`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!res.ok) {
        let message = `HTTP ${res.status}`;
        try {
          const errorData = await res.json();
          if (errorData?.detail) message = errorData.detail;
        } catch {}
        onImportError(message);
        return;
      }

      const result: ImportResult = await res.json();
      onImportSuccess(result);
    } catch {
      onImportError("Failed to import file. Please try again.");
    }
  };

  return (
    <HStack gap={0}>
      <FileUpload.Root
        accept={{ "*/*": [".csv"] }}
        maxFiles={1}
        maxFileSize={1e7}
        onFileAccept={({ files }) => handleFileAccept(files)}
        onFileReject={(details) =>
          onImportError(`Invalid file: ${details.files[0].errors.join(", ")}`)
        }
      >
        <FileUpload.HiddenInput />
        <FileUpload.Trigger asChild>
          <Button
            colorPalette="teal"
            variant="ghost"
            aria-label="Import a previously downloaded dataset"
          >
            <LuFileUp /> Import
          </Button>
        </FileUpload.Trigger>
      </FileUpload.Root>
      <Text textWrap="nowrap">a previous download</Text>
    </HStack>
  );
}
