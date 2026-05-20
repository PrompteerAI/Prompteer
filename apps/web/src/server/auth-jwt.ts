import {
  createPrivateKey,
  createPublicKey,
  createSign,
  createVerify,
  generateKeyPairSync,
  randomUUID,
  type KeyObject,
} from "node:crypto";

import type { JWT, JWTDecodeParams, JWTEncodeParams } from "next-auth/jwt";

const DEFAULT_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;
const JWT_ALGORITHM = "RS256";

interface AuthJwtClaims extends JWT {
  iss: string;
  aud: string;
  iat: number;
  exp: number;
  jti: string;
}

interface AuthJwtKeyPair {
  privateKey: KeyObject;
  publicKey: KeyObject;
}

let cachedKeyPair: AuthJwtKeyPair | undefined;

export function encodeAuthJwt(params: JWTEncodeParams): string {
  const now = Math.floor(Date.now() / 1000);
  const maxAge = params.maxAge ?? DEFAULT_MAX_AGE_SECONDS;
  const token = params.token ?? {};
  const payload: AuthJwtClaims = {
    ...token,
    iss: authJwtIssuer(),
    aud: authJwtAudience(),
    iat: now,
    exp: now + maxAge,
    jti: typeof token.jti === "string" ? token.jti : randomUUID(),
  };
  return signJwt(payload);
}

export function decodeAuthJwt(params: JWTDecodeParams): JWT | null {
  if (!params.token) {
    return null;
  }

  const [encodedHeader, encodedPayload, encodedSignature] =
    params.token.split(".");
  if (!encodedHeader || !encodedPayload || !encodedSignature) {
    return null;
  }

  const signingInput = `${encodedHeader}.${encodedPayload}`;
  const verifier = createVerify("RSA-SHA256");
  verifier.update(signingInput);
  verifier.end();
  const isValid = verifier.verify(
    getAuthJwtKeyPair().publicKey,
    encodedSignature,
    "base64url",
  );
  if (!isValid) {
    return null;
  }

  const payload = JSON.parse(
    Buffer.from(encodedPayload, "base64url").toString("utf8"),
  ) as JWT;
  const expiresAt = typeof payload.exp === "number" ? payload.exp : 0;
  if (expiresAt <= Math.floor(Date.now() / 1000)) {
    return null;
  }
  if (payload.iss !== authJwtIssuer() || payload.aud !== authJwtAudience()) {
    return null;
  }
  return payload;
}

export function getAuthJwtPublicJwk(): JsonWebKey & {
  alg: "RS256";
  kid: string;
  use: "sig";
} {
  const jwk = getAuthJwtKeyPair().publicKey.export({ format: "jwk" });
  return {
    ...jwk,
    alg: JWT_ALGORITHM,
    kid: authJwtKeyId(),
    use: "sig",
  };
}

function signJwt(payload: AuthJwtClaims): string {
  const header = {
    alg: JWT_ALGORITHM,
    kid: authJwtKeyId(),
    typ: "JWT",
  };
  const signingInput = `${base64urlJson(header)}.${base64urlJson(payload)}`;
  const signer = createSign("RSA-SHA256");
  signer.update(signingInput);
  signer.end();
  return `${signingInput}.${signer.sign(getAuthJwtKeyPair().privateKey, "base64url")}`;
}

function getAuthJwtKeyPair(): AuthJwtKeyPair {
  if (cachedKeyPair) {
    return cachedKeyPair;
  }

  const privateKeyPem = process.env.AUTH_JWT_PRIVATE_KEY?.replaceAll(
    "\\n",
    "\n",
  ).trim();
  if (privateKeyPem) {
    const privateKey = createPrivateKey(privateKeyPem);
    cachedKeyPair = { privateKey, publicKey: createPublicKey(privateKey) };
    return cachedKeyPair;
  }

  cachedKeyPair = generateKeyPairSync("rsa", { modulusLength: 2048 });
  return cachedKeyPair;
}

function base64urlJson(value: unknown): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function authJwtIssuer(): string {
  return (
    process.env.AUTH_JWT_ISSUER ||
    process.env.AUTH_URL ||
    "http://localhost:3000"
  ).replace(/\/+$/, "");
}

function authJwtAudience(): string {
  return process.env.AUTH_JWT_AUDIENCE || "prompteer-api";
}

function authJwtKeyId(): string {
  return process.env.AUTH_JWT_KEY_ID || "prompteer-dev-auth";
}
