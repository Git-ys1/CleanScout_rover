ALTER TABLE "MessageCache" ADD COLUMN "type" TEXT NOT NULL DEFAULT 'text';
ALTER TABLE "MessageCache" ADD COLUMN "imageUrl" TEXT;
ALTER TABLE "MessageCache" ADD COLUMN "imageName" TEXT;
ALTER TABLE "MessageCache" ADD COLUMN "mimeType" TEXT;
