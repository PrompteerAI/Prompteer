// Unit tests for legacy-preview data mapping and API fallback behavior.
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiClientMocks = vi.hoisted(() => ({
  get: vi.fn(),
  unwrap: vi.fn((result: { data?: unknown }) => result.data),
}));

vi.mock("./api-client", () => ({
  createPrompteerApiClient: () => ({ GET: apiClientMocks.get }),
  unwrapApiResponse: apiClientMocks.unwrap,
}));

import { readBoardPost, readBoardShare, type Post, type Share } from "./data";

const post = {
  id: "post-1",
  type: "question",
  tag: "ps",
  title: "How should I approach this?",
  content: "I need help with prompt structure.",
  author: {
    id: "user-1",
    display_name: "Ada",
    plan: "free",
  },
  challenge: null,
  created_at: "2026-05-20T03:04:05Z",
} satisfies Post;

const share = {
  id: "share-1",
  prompt: "Explain the solution step by step.",
  is_public: true,
  author: {
    id: "user-2",
    display_name: "Grace",
    plan: "pro",
  },
  challenge: {
    id: "challenge-2",
    challenge_number: 2,
    tag: "img",
    level: "easy",
    title: "Image prompt",
  },
  created_at: "2026-05-21T03:04:05Z",
} satisfies Share;

describe("board detail data readers", () => {
  beforeEach(() => {
    apiClientMocks.get.mockReset();
    apiClientMocks.unwrap.mockReset();
    apiClientMocks.unwrap.mockImplementation(
      (result: { data?: unknown }) => result.data,
    );
  });

  it("reads a board post from the post detail endpoint", async () => {
    apiClientMocks.get.mockResolvedValue({ data: post });

    await expect(readBoardPost("post-1")).resolves.toBe(post);

    expect(apiClientMocks.get).toHaveBeenCalledWith(
      "/api/v1/community/posts/{post_id}",
      {
        params: { path: { post_id: "post-1" } },
        cache: "no-store",
      },
    );
  });

  it("reads a shared prompt from the share detail endpoint", async () => {
    apiClientMocks.get.mockResolvedValue({ data: share });

    await expect(readBoardShare("share-1")).resolves.toBe(share);

    expect(apiClientMocks.get).toHaveBeenCalledWith(
      "/api/v1/community/shares/{share_id}",
      {
        params: { path: { share_id: "share-1" } },
        cache: "no-store",
      },
    );
  });
});
