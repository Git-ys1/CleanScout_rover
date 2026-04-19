-- CreateTable
CREATE TABLE "EdgeDevice" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "deviceId" TEXT NOT NULL,
    "tokenHash" TEXT NOT NULL,
    "isEnabled" BOOLEAN NOT NULL DEFAULT true,
    "transport" TEXT NOT NULL DEFAULT 'edge-relay',
    "topicsJson" TEXT NOT NULL DEFAULT '{}',
    "capabilitiesJson" TEXT NOT NULL DEFAULT '[]',
    "lastSeenAt" DATETIME,
    "lastHelloAt" DATETIME,
    "lastDisconnectAt" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "EdgeDevice_deviceId_key" ON "EdgeDevice"("deviceId");
