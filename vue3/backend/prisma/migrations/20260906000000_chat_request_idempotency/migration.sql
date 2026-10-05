CREATE TABLE "ChatRequest" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "userId" TEXT NOT NULL,
  "requestId" TEXT NOT NULL,
  "fingerprint" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'processing',
  "claim" TEXT NOT NULL,
  "response" TEXT,
  "updatedAt" DATETIME NOT NULL,
  CONSTRAINT "ChatRequest_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE UNIQUE INDEX "ChatRequest_userId_requestId_key" ON "ChatRequest"("userId", "requestId");
