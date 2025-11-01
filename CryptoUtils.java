import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.spec.AlgorithmParameterSpec;

import javax.crypto.Cipher;
import javax.crypto.CipherInputStream;
import javax.crypto.CipherOutputStream;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class CryptoUtils {
    // 1. 密钥和算法参数
    // AES 128 位需要 16 字节的 Key
    private static final String KEY_STRING = "b3c9a0f4e2d1c6b5";
    // IV (Initialization Vector) 必须是 16 字节，用于 CBC 模式
    private static final String IV_STRING = "f6e5d4c3b2a19870";

    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";

    private static SecretKeySpec getSecretKeySpec() {
        return new SecretKeySpec(KEY_STRING.getBytes(), ALGORITHM);
    }

    private static AlgorithmParameterSpec getIvSpec() {
        return new IvParameterSpec(IV_STRING.getBytes());
    }

    /**
     * 执行文件加密或解密的核心逻辑
     *
     * @param cipherMode Cipher.ENCRYPT_MODE 或 Cipher.DECRYPT_MODE
     * @param input      Input 文件或资源流
     * @param output     Output 文件流
     * @throws Exception 加密/解密过程中的异常
     */
    private static void processFile(int cipherMode, InputStream input, OutputStream output) throws Exception {
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(cipherMode, getSecretKeySpec(), getIvSpec());

        // 使用 CipherStream 边读边处理，节省内存
        InputStream cis = null;
        OutputStream cos = null;

        if (cipherMode == Cipher.ENCRYPT_MODE) {
            // 加密模式：普通 InputStream -> CipherOutputStream -> FileOutputStream
            cos = new CipherOutputStream(output, cipher);
            byte[] buffer = new byte[4096];
            int len;
            while ((len = input.read(buffer)) != -1) {
                cos.write(buffer, 0, len);
            }
            cos.flush();

        } else if (cipherMode == Cipher.DECRYPT_MODE) {
            // 解密模式：FileInputStream -> CipherInputStream -> 普通 OutputStream
            cis = new CipherInputStream(input, cipher);
            byte[] buffer = new byte[4096];
            int len;
            while ((len = cis.read(buffer)) != -1) {
                output.write(buffer, 0, len);
            }
            output.flush();
        }

        if (cis != null) cis.close();
        if (cos != null) cos.close();
    }

    // --- 对外提供的接口 ---

    /**
     * **[已修改]** 对文件进行加密
     * * @param inputPath 原始文件的路径 (e.g., /path/to/classes.dex)
     *
     * @param outputPath 加密后的文件的路径 (e.g., /path/to/plugin_v1.dat)
     */
    public static void encryptFile(String inputPath, String outputPath) throws Exception {
        File inputFile = new File(inputPath);
        File outputFile = new File(outputPath);

        // 确保输出目录存在
        if (outputFile.getParentFile() != null && !outputFile.getParentFile().exists()) {
            outputFile.getParentFile().mkdirs();
        }

        try (FileInputStream fis = new FileInputStream(inputFile); FileOutputStream fos = new FileOutputStream(outputFile)) {

            processFile(Cipher.ENCRYPT_MODE, fis, fos);
        }
    }

    /**
     * 对文件进行解密 (通常用于宿主应用内部，接收 InputStream)
     *
     * @param inputStream 加密文件的输入流 (e.g., assets 中的 plugin_v1.dat)
     * @param outputFile  解密后的文件 (e.g., plugin_classes.dex)
     */
    public static void decryptFile(InputStream inputStream, File outputFile) throws Exception {
        // 确保输出目录存在
        if (outputFile.getParentFile() != null && !outputFile.getParentFile().exists()) {
            outputFile.getParentFile().mkdirs();
        }

        try (FileOutputStream fos = new FileOutputStream(outputFile)) {

            processFile(Cipher.DECRYPT_MODE, inputStream, fos);
        }
    }

    public static void main(String[] args) {
        //CryptoUtils utils = new CryptoUtils();
        String path = "G:/OriginProject/TestApplication/mylibrary/build/outputs/dex/classes.dex";
        String output = "G:/OriginProject/TestApplication/mylibrary/build/outputs/dex/plugin_v1.dat";
        try {
            CryptoUtils.encryptFile(path,output);
            System.out.println("加密完成");
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
