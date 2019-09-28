import cv2
import numpy as np
import glob


def image_stitch():
    all_images = []
    all_images.extend(glob.glob('images/' + '*.jpg'))
    all_images.sort()

    result = cv2.imread(all_images[0])
    for index, image in enumerate(all_images):
        if index is 0:
            continue

        img1 = result
        img2 = cv2.imread(all_images[index])

        sift = cv2.xfeatures2d.SIFT_create()
        # find key points
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)

        match = cv2.BFMatcher(crossCheck=True)
        matches = match.match(des1, des2)
        good = sorted(matches, key=lambda x: x.distance)[:100]

        draw_params = dict(matchColor=(0, 255, 0),
                           singlePointColor=None,
                           flags=2)

        img3 = cv2.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)
        cv2.imwrite('draw{}.jpg'.format(index), img3)

        if len(good) < 40:
            print("Not enough matches found: ", len(good))
            return

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        h, w = img2.shape[:2]
        h2, w2 = img1.shape[:2]

        pts1 = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
        pts2 = np.float32([[0, 0], [0, h2], [w2, h2], [w2, 0]]).reshape(-1, 1, 2)
        pts1 = cv2.perspectiveTransform(pts1, M)

        pts = np.concatenate((pts1, pts2), axis=0)

        [xmin, ymin] = np.int32(pts.min(axis=0).ravel() - 0.5)
        [xmax, ymax] = np.int32(pts.max(axis=0).ravel() + 0.5)
        t = [-xmin, -ymin]

        Ht = np.array([[1, 0, t[0]], [0, 1, t[1]], [0, 0, 1]])  # translate

        # img2 = cv2.polylines(img2, [np.int32(cv2.perspectiveTransform(pts, M))], True, 255, 3, cv2.LINE_AA)
        # cv2.imshow('poly', img2)

        result = cv2.warpPerspective(img1, Ht.dot(M), (xmax - xmin, ymax - ymin))
        result[t[1]:h + t[1], t[0]:w + t[0]] = img2

    cv2.imwrite('result.jpg', result)
    # cv2.waitKey(0)


image_stitch()
