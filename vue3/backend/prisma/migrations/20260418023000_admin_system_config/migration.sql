ALTER TABLE "User" ADD COLUMN "isEnabled" BOOLEAN NOT NULL DEFAULT true;

CREATE TABLE "SystemConfig" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "registrationEnabled" BOOLEAN NOT NULL DEFAULT true,
    "appEnabled" BOOLEAN NOT NULL DEFAULT true,
    "maintenanceMessage" TEXT NOT NULL DEFAULT '',
    "openclawEnabled" BOOLEAN NOT NULL DEFAULT false,
    "updatedAt" DATETIME NOT NULL
);
